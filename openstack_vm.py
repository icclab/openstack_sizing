# -*- coding: utf-8 -*-
"""
Created on Wed May 14 15:07:06 2014

@author: konstantin
"""

#!/usr/bin/env python
import os as current
import struct
import sys
import time
import subprocess
import os.path

from multiprocessing import Process, Pool

import keystoneclient.v2_0.client as ksclient
from novaclient import client as novaclient

from credentials import set_creds, get_nova_creds

from fabric.api import *
##from netaddr import *


# TODO: put credentials in encrypted file


def get_openstack_clients(username="your_openstack_username",
                          password="your_openstack_password",
                          auth_url="http://<your_openstack_url>:35357/v2.0",
                          tenant="your_openstack_tenantname"):
        set_creds(username=username,
                  password=password,
                  auth_url=auth_url,
                  tenant=tenant,
                  current_os=current)
        nova_creds = get_nova_creds(current_os=current)
        nova = novaclient.Client("1.1", **nova_creds)
        return nova


def create_keypairs(nova,
		keypair_name='mykey',
		keyfile_path='id_rsa.pub'):
        print('Generating keypairs: %s' % keypair_name)
        if not nova.keypairs.findall(name=keypair_name):
                with open(current.path.expanduser(str(keyfile_path))) as fpubkey:
                        print('Generating...')
                        nova.keypairs.create(name=keypair_name,
                                             public_key=fpubkey.read())
        mykey=nova.keypairs.find(name=keypair_name)
        print('Generated keypair: %s' % mykey)
        return mykey


def create_sec_rules(nova):
        print('Creating security group rules')
        secgroup = nova.security_groups.find(name='default')
        if not secgroup.rules:
                print('Does not exist')
                nova.security_group_rules.create(secgroup.id,
                                 ip_protocol="tcp",
                                 from_port=22,
                                 to_port=22)
                nova.security_group_rules.create(secgroup.id,
                                 ip_protocol="icmp",
                                 from_port=-1,
                                 to_port=-1)

"""
Creates a group of VM test instances
"""
def create_instance_group(nova,
                          mykey="mykey",
                          image_name="Sizing_Test_Instance",
                          flavor_name="m1.large",
                          num_vms=10):
        image = nova.images.find(name=image_name)
        flavor = nova.flavors.find(name=flavor_name)
        vm_list = []
        for x in range(1,num_vms+1):
                instance_name = str('load_vm%s' % x)
                try:
                        instance = nova.servers.find(name=instance_name)
                        print("Instance already exists.")
                except:
                        instance = nova.servers.create(name=instance_name,
                                                       image=image,
                                                       flavor=flavor,
                                                       key_name=mykey)
                status = instance.status
                trials = 0
                # Start new VM and repeatedly poll if VM is started. Exit in case of error.
                while status != 'ACTIVE':
                        if status == 'ACTIVE':
                                break
                        if status == 'ERROR' or status == 'SHUTOFF':
                                instance.delete()                              
                                if trials < 3:
                                        instance = nova.servers.create(name=instance_name,
                                                       image=image,
                                                       flavor=flavor,
                                                       key_name=mykey,
                                                                       )
                                        time.sleep(5)
                                        trials +=1
                                        print("BUILD ERROR occurred. Recovery trial: %s" % trials)
                                else:
                                        time.sleep(5)
                                        break
                        time.sleep(5)
                        print("Building instance: %s" % instance.id)
                        print("status: %s" % status)
                        # Retrieve the instance again so the status field updates
                        instance = nova.servers.get(instance.id)
                        status = instance.status
                else:
                        vm_list.append(instance)
        print(vm_list)
        return vm_list

def assign_floating_ips_to_instance_group(vm_list,nova):
        floating_ips_list = []
        for instance in vm_list:
                if not nova.floating_ips.findall(instance_id=instance.id):
                        floating_ip = nova.floating_ips.create()
                        instance.add_floating_ip(floating_ip)
                        time.sleep(1)
                        floating_ip = nova.floating_ips.find(instance_id=instance.id)
                        print("Created Floating IP: %s for instance %s" % (floating_ip.ip,
                                                                           floating_ip.instance_id))
                else:
                        floating_ip = nova.floating_ips.find(instance_id=instance.id)
                        instance.add_floating_ip(floating_ip)
                        time.sleep(1)
                        floating_ip = nova.floating_ips.find(instance_id=instance.id)
                        print("Existing Floating IP: %s for instance %s" % (floating_ip.ip,
                                                                           floating_ip.instance_id))
                if floating_ip.instance_id != None:
                        floating_ips_list.append(floating_ip)
        print(floating_ips_list)
        return floating_ips_list

def reassign_floating_ip_to_instance(instance, nova):
        if nova.floating.ips.findall(instance_id=instance.id):
                floating_ip = nova.floating_ips.find(instance_id=instance.id)
        else:
                floating_ip = nova.floating_ips.create()
        instance.remove_floating_ip(floating_ip)
        print("Removed Floating IP: %s" % floating_ip.ip)
        instance.add_floating_ip(floating_ip)
        print("Added Floating IP: %s" % floating_ip.ip)

def print_sorted_ips(floating_ips_list):
        float_ips = {}
        for float_ip in floating_ips_list:
                D = {str(float_ip.ip): str(float_ip)}
                float_ips.update(D)
        return float_ips

##secgroup = nova.security_groups.find(name="default")

def delete_all_floating_ips(nova):
        for ip in nova.floating_ips.findall():
                print('Deleting ip %s' % ip)
                try:
                        ip.delete()
                        print('Deleted ip %s' % ip)
                except Exception as e:
                        print "Error({0}): {1}".format(e.errno, e.strerror)


def delete_all_instances(nova):
        for instance in nova.servers.findall():
                status = instance.status
                if status == 'ACTIVE':
                        instance.stop()
                print("Stopping instance '%s' with id: %s" %
                      (instance.name, instance.id))
                while status == 'ACTIVE':
                        print(instance.status)
                        time.sleep(5)
                        instance = nova.servers.get(instance.id)
                        status = instance.status
                print('Deleting instance %s' % instance.id)
                try:
                        instance.delete()
                except Exception as e:
##                        print "Error({0}): {1}".format(e.errno, e.strerror)
                        pass
                
"""
Create a hosts file that stores IPs of all test VMs that were created.
"""
def create_hosts_file(float_ips,filename='hosts'):
        hostfile = open(filename,'w')
        hostfile.write('')
        hostfile.close()
        hostfile = open(filename,'w')
        print(type(float_ips))
        print(type([]))
        print(type({}))
        if type(float_ips)==type({}):
                print 'bla'
                for item in float_ips.keys():
                        hostfile.write(item+'\n');print(item)
        if type(float_ips)==type([]):
                for item in float_ips:
                        hostfile.write(item+'\n');print(item)
        hostfile.close()

"""
Helper method to run remote tasks on test VMs.
"""
def run_fab_task(task, fabfile='fabfile.py'):
        task = "fab -f "+ fabfile +" " + task
        print('running task'+task)
        message = subprocess.Popen(task, shell=True, stdout=subprocess.PIPE)
        print('1')
        output = message.stdout.read()
        print('2')
        message.stdout.close()
        message.wait()
        print(output)

"""
Helper method to run remote tasks on test VMs which accepts 2
arguments, remote and local path.
"""
def run_fab_taski(task, localpath, remotepath, fabfile='fabfile.py'):
        task = str("fab -f %s %s:%s,%s" % (fabfile, task, localpath, remotepath))
        print('running task'+task)
        message = subprocess.Popen(task, shell=True, stdout=subprocess.PIPE)
        print('1')
        output = message.stdout.read()
        print('2')
        message.stdout.close()
        message.wait()
        print(output)


def get_fixed_ips(vm_list, nova):
        fixed_ips_list = []
        for instance in vm_list:
                fixed_ip = nova.fixed_ips.get(instance.addresses[u'novanetwork'][0][u'addr'])
                print("Existing fixed IP: %s for instance %s" % (str(fixed_ip.address),
                                                                           str(fixed_ip.to_dict()[u'hostname'])))
                fixed_ips_list.append(str(fixed_ip.address))
        print(fixed_ips_list)
        return fixed_ips_list

def set_up(num_vms=10,flavor_name="m1.large"):
        nova = get_openstack_clients()
        print(nova.keypairs.list())
        print(current)
        mykey = create_keypairs(nova)
        create_sec_rules(nova)
        print(mykey)
        vm_list = create_instance_group(nova,num_vms=num_vms,flavor_name=flavor_name)
        print(vm_list)
        float_ips = assign_floating_ips_to_instance_group(vm_list, nova)
##        float_ips = print_sorted_ips(float_ips)
        create_hosts_file(float_ips)
        return float_ips, nova

def configure(float_ips):
        float_ips=[str(line).rstrip() for line in open('hosts').readlines()]
        print(float_ips)
        run_fab_task('ssh_config')
##        run_fab_task('install_sshpass')
##        run_fab_task('install_pip')
##        run_fab_task('update')
##        run_fab_task('install_dev')
##        run_fab_task('install_python_pckg')

        run_fab_task('assign_hostname')
        run_fab_taski('file_send', 'pi_compute.py', 'pi_compute.py')      
        run_fab_taski('file_send', 'token', 'token')


def get_free_fixed_ips(nova, ips):
        return [str(ip) for ip in ips if not nova.floating_ips.findall(fixed_ip=str(ip))]

def is_fixed_ip_free(nova, ip):
        return (not nova.floating_ips.findall(fixed_ip=str(ip)))

def get_remote_logs(float_ips, logname='log.csv'):
        run_fab_task('get_log')
        try:
                if os.path.isfile(logname) == False:
                        consolidated_log = open(logname,'w')
                        consolidated_log.write('Instance,TimeStamp,Duration,CPU.Usage,Memory.Usage,Bytes.Sent,Bytes.Recv\n')
                else:
                        print("File exists in %s: %s"%(logname,float_ips))
                        consolidated_log = open(logname,'a')
                for ip in float_ips:
                        [consolidated_log.write(str(line).rstrip()+'\n') for line in open(str('%s.log.txt' % ip)).readlines() if os.path.isfile(str('%s.log.txt' % ip))]
                consolidated_log.close()
        except Exception as e:
                print "Error({0}): {1}".format(e.errno, e.strerror)



def run(num_vms,flavor_name="m1.large"):
        float_ips,nova=set_up(num_vms=num_vms,flavor_name=flavor_name)
        float_ips=[str(line).rstrip() for line in open('hosts').readlines()]
        configure(float_ips)
        return nova,float_ips

def collect_data(float_ips,task='compute_pi',logfile='log.csv'):
        run_fab_task(task)
        get_remote_logs(float_ips,logfile)

def clear(nova):
        delete_all_instances(nova)
        delete_all_floating_ips(nova)  

def main():
        float_ips,nova=set_up(num_vms=15,flavor_name="m1.large")
        float_ips=[str(line).rstrip() for line in open('hosts').readlines()]
        configure(float_ips)
        run_fab_task('broadcast_file')
        get_remote_logs(float_ips)
        return nova,float_ips                      


if  __name__ =='__main__':
        nova,float_ips=main()
