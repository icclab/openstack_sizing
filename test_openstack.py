import openstack_vm as runner
import random, time

"""test_openstack.py
This class runs the VMs and tests the OpenStack performance.
"""

start = time.time()
for r in range(1):
    task_name = 'compute_pi'
    print("Task name = %s" % task_name)
    flavors={
    '3':'m1.large',
    '2':'m1.medium',
    '4':'m1.xlarge',
    '1':'m1.small'
    }
    flavor_num = list(range(1,len(flavors)+1))
    for i in flavor_num:
        print(flavor_num)
        print("Flavor number = " % flavor_num)
        flavor_key = random.choice(flavors.keys())
        flavor_name = flavors.pop(flavor_key)
        print("Flavor name = %s" % flavor_name)
        print(flavor_num)
        vm_num = range(2,20)
        stat_vm_num = list(vm_num)
        for j in stat_vm_num:
            print(stat_vm_num)
            print(vm_num)
            vm_value = random.choice(vm_num)
            print(vm_value)
            print(vm_num)
            vm_key = vm_num.index(vm_value)
            print(vm_key)
            num_vms = vm_num.pop(vm_key)
            print(vm_num)
            print(stat_vm_num)
            nova = runner.get_openstack_clients()
            runner.clear(nova)
            print("Num VMs = %s" % num_vms)
            nova, float_ips = runner.run(num_vms=num_vms,flavor_name=flavor_name)
            logfile_name = str('log.%s.%s.%s.csv' % (num_vms , flavor_name, task_name))
            runner.collect_data(float_ips,task=task_name,logfile=logfile_name)
            runner.clear(nova)
elapsed_time = time.time() - start
print("VM Tests finished in: %s s." % elapsed_time)
