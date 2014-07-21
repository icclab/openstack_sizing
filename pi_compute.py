import math
import subprocess,random,sys,getopt
import time, psutil, socket
from decimal import *

"""pi_compute.py

This module computes Pi in a given number of steps.
"""


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
    for arg in args:
        steps=int(arg)
    pi(steps)


def pi(steps):
    print('\nComputing Pi v.01\n')
    a = Decimal(1.0)
    b = Decimal(1.0/math.sqrt(2))
    t = Decimal(1.0)/Decimal(4.0)
    p = Decimal(1.0)

    start = time.time()
    cpu_usage_list = []
    vmem_usage_list = []
    sent_bytes_list = []
    recv_bytes_list = []

    for i in range(steps):
        send1 = get_sent_bytes()
        recv1 = get_recv_bytes()
        cpu_usage_list.append(get_cpu_usage())
        vmem_usage_list.append(get_vmem_usage())
        at = Decimal((a+b)/2)
        bt = Decimal(math.sqrt(a*b))
        tt = Decimal(t - p*(a-at)**2)
        pt = Decimal(2*p)
        a = at;b = bt;t = tt;p = pt
        
        send1 = get_sent_bytes()-send1
        recv1 = get_recv_bytes()-recv1
        sent_bytes_list.append(send1)
        recv_bytes_list.append(recv1)

    my_pi = (a+b)**2/(4*t)
    accuracy = 100*(abs(Decimal(math.pi)-my_pi))/my_pi

    end = time.time()
    time_elapsed = end - start
    cpu_usage = average(cpu_usage_list)
    vmem_usage = average(vmem_usage_list)
    network_sent_bytes = average(sent_bytes_list)
    network_recv_bytes = average(recv_bytes_list)

    print("Pi is approximately:  %s" % str(my_pi))
    print("Accuracy is approximately: %s" % str(accuracy))

    myname = open('/home/icclab/myname','r').read().rstrip()
    logfile = open('/home/icclab/log.txt','a')
    logfile.write('%s,%s,%.3f,%.3f,%.3f,%.3f,%.3f\n' % (myname,
                                                         start,
                                                        time_elapsed,
                                                        cpu_usage,
                                                        vmem_usage,
                                                        network_sent_bytes,
                                                        network_recv_bytes))
    logfile.close()

"""
Util methods for measurements.
"""

def get_cpu_usage():
        cpu_time = psutil.cpu_times()
        cpu_usage = 100 * (1 - cpu_time.idle/
                           (cpu_time.system +
                            cpu_time.user +
                            cpu_time.iowait +
                            cpu_time.irq +
                            cpu_time.nice +
                            cpu_time.softirq +
                            cpu_time.idle))
        return cpu_usage

def get_vmem_usage():
        vmem = psutil.virtual_memory()
        vmem_percent = float(vmem.free * 100)/float(vmem.total)
        vmem_percent = float(100) - vmem_percent
        return vmem_percent

def get_sent_bytes():
        network = psutil.network_io_counters()
        return network.bytes_sent

def get_recv_bytes():
        network = psutil.network_io_counters()
        return network.bytes_recv

def average(some_list):
        return float(sum(some_list))/float(len(some_list))

if  __name__ =='__main__':
    main()
