openstack_sizing
================

Python Code to perform OpenStack sizing tests. 
The test script starts a (pre-defined) number of OpenStack VMs, lets the VMs compute the number Pi and logs the time taken by computation job as well as CPU and memory usage. Afterwards it consolidates usage data in a central log file and destroys the VMs again.
The collected data can be used for analysis of:
* How many VMs can be created on an OpenStack instance
* How many VMs can run in parallel on an OpenStack instance without significant performance decrease
* How the performance of indivdual VMs changes if VMs are added or removed
* How many VMs would run "ideally" on the tested OpenStack instance
