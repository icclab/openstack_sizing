# -*- coding: utf-8 -*-
"""
#################################################################
#################################################################
#
# Copyright (c) 2014 by
# Zürcher Hochschule der Angewandten Wissenschaften (ZHAW)
#
# Author:      Konstantin Benz
# Created:     13/07/13   
# Last update: 14/07/13
#
# Fabric file
# -------------------
#
# This fabfile is required to perform sizing test actions
# on OpenStack. It is the interface between test script and VMs.
#
# The following actions can be done:
# - Send files to VMs / get files from VMs
# - Install and upgrade packages including Python on VMs
# - Run Pi computation file
#
#################################################################
#################################################################
"""

from fabric.api import *

env.user = 'vm_user'
env.password  = 'vm_host'
env.hosts = [str(line).rstrip() for line in open('hosts').readlines()]
env.skip_bad_hosts = False
env.timeout = 2
env.warn_only = True

def file_send(localpath,remotepath):
    output = put(localpath,remotepath,use_sudo=True)
    print output

def file_send_mod(localpath,remotepath,mod):
    put(localpath,remotepath,mode=int(mod, 8))

def file_get(remotepath, localpath):
    get(remotepath,localpath+"."+env.host)

def get_log():
    get('log.txt',env.host+".log.txt")


def assign_hostname():
    sudo("rm -rf myname")
    sudo("touch myname")
    sudo("echo %s >> myname" % env.host)


def update():
    output = sudo("apt-get -y update")
    print output


def install_zip():
    output = sudo("apt-get -y install zip")
    print output
    

def install_sshpass():
    output = sudo("apt-get -y install sshpass")
    print output


def install_pip():
    output = sudo("apt-get -y install python-pip")
    print output


def install_dev():
    output = sudo("apt-get -y install python-dev")
    print output


def install_python_pckg():
    sudo("pip install psutil")
    sudo("pip install fabric")
    sudo("pip install numpy")


def ssh_config():
    output = put("id_rsa.pub","id_rsa.pub", use_sudo=True)
    print output

@parallel(pool_size=len(env.hosts))
def broadcast_file():
    output = sudo('python broadcaster.py 128')
    print output

@parallel(pool_size=10)
def broadcast_large_file():
    output = sudo('python broadcaster.py 10240')
    print output

@parallel(pool_size=10)
def broadcast_larger_file():
    output = sudo('python broadcaster.py 100240')
    print output

@parallel(pool_size=len(env.hosts))
def compute_pi():
    output = sudo('python pi_compute.py 40960')
    print output
