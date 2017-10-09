# netengtools
These are examples of network automation tools written in python3.4+ that support traditional multi-tenant hosting environments. They are as follows:

1. boreasprov.py - A tool to automatically generate switchport configs, custom cabling instructions, all the relevant resource allocations in a form.
2. flexcabling.py - A tool that generates custom server-side cabling instructions and switchport configurations.
These tools are posted at GitHub for demonstration purposes only.

The foundations of these tools are the custom libraries (2) Loccode and (2) NWdevice. Location codes uniquely define server site/room/rack/slot locations at multiple data centers. In my sample library, two fictitious sites "IAD" and "SJC" are defined. Network devices typically use only some of the racks and the rest of the racks are used by servers (compute nodes). By cutomizing LocCode, one can adjust the library to their unique data center designs. Network device names are also uniquely defined in every hosting provider environment, and my sample library defines firewalls and load balancers. Again, one can define network devices to meet their own environment.

3. backup.py - A tool that collects config dumps from various Cisco gears by using pexpect. A small static database file device_lists.py has a list of fictitious device names and they are grouped by Cisco IOS types (IOS, ASA, IOS-XE, IOS-XR, etc.) and single context ASAs versus multi-context ASAs. Even a hosting provider may be able to cover all of their network devices with such a simple database file. 
