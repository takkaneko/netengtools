#!/usr/bin/env python3
# ipsprov.py

# Use this option in case an IPS monitors two different 
# network devices where the devices can be either HA gears 
# or stand-alone gears.

# Also use in case an IPS aims at monitoring an HA *standby*
# gear (This is not common).

import re
from locationcode import Loccode
from networksid import NWdevice
from resources import getUPA
from resources import getInterfaceIP
from resources import devicePorts
from resources import getIPS
from resources import getIPSmgtInfo
from resources import getNWdevice
from resources import getItf_and_port
from resources import showIPSCabling

def main():
    ##### Warning Message:
    warning = 'THIS OPTION SHOULD ONLY BE USED FOR RARE CASES WHERE AN IPS \n'
    warning += 'NEEDS TO MONITOR SEGMENTS FROM TWO DIFFERENT NETWORK DEVICES, \n'
    warning += 'OR TO MONITOR A SECONDARY (STANDBY) DEVICE.\n\n'
    print(warning)    
    
    ##### Prompts to enter username, password, and allocation code:
    [username,password,alloccode] = getUPA()
    
    ##### Prompt to enter IPS SID and Location:
    [ips,ipsloc] = getIPS()
    
    ##### Prompt to enter IPS mgmt VLAN, depthcode, and mgmt IP:
    [ipsmgtVlan,ipsmgtDepth,ipsmgtIPaddr] = getIPSmgtInfo()
    
    ##### Prompt to enter the network device #1 SID and Location:
    [nwdevice1,speed1,nwdevice1loc] = getNWdevice(1,ipsloc)
    
    ##### Prompt to enter the device #1's monitored segment info:
    [segmentName1,deviceitf1,swport1,pnum1] = getItf_and_port(nwdevice1,nwdevice1loc)

    ##### Prompt to enter the network device #2 SID and Location:
    while True:
        [nwdevice2,speed2,nwdevice2loc] = getNWdevice(2,ipsloc)
        if nwdevice2 != nwdevice1 and nwdevice2loc == nwdevice1loc:
            print('ERROR: '+nwdevice2.upper()+' AND '+nwdevice1.upper()+' CANNOT TAKE THE SAME LOCATION.\n')
            print('Re-enter the device #2 name/speed/location information again.\n')
        elif nwdevice2 == nwdevice1 and nwdevice2loc != nwdevice1loc:
            print('ERROR: LOCATION MISMATCH FOUND FOR '+nwdevice1+'.\n')
            print('Re-enter the device #2 name/speed/location information again.\n')
        else:
            break
    
    ##### Prompt to enter the device #2's monitored segment info:
    while True:
        [segmentName2,deviceitf2,swport2,pnum2] = getItf_and_port(nwdevice2,nwdevice2loc)
        if segmentName1.lower() == segmentName2.lower():
            print('ERROR: THE SEGMENT NAME ALREADY EXISTS.\n')
            print('Re-enter the device #2 segment/interface/port information again.\n')
        elif nwdevice1 == nwdevice2 and deviceitf2 == deviceitf1:
            print('ERROR: THE INTERFACE IS ALREADY SELECTED.\n')
            print('Re-enter the device #2 segment/interface/port information again.\n')
        elif nwdevice1 == nwdevice2 and swport2 == swport1:
            print('ERROR: THE SWITCHPORT IS ALREADY SELECTED.\n')
            print('Re-enter the device #2 segment/interface/port information again.\n')
        else:
            break

    #############################################################################
    print('\nThe rest will generate port configs, custom cabling info, allocation form, etc.\n')
    
    # back up port configs
    print('******************************************************')
    print('Use the following to collect switchport backup configs')
    print('******************************************************\n')

    backup = 'telnet '+ipsloc.findsw()+'\n'
    backup += username+'\n'
    backup += password+'\n'
    backup += 'sh run int '+ipsloc.findfrport()+'\n'
    backup += 'sh run int '+ipsloc.findbkport()+'\n'
    backup += 'exit\n'
    print(backup)

    input('Hit Enter to view the new switchport configs.')
    print()
    # new port configs
    print('*************************************************')
    print('Use the following to apply new switchport configs')
    print('*************************************************\n')
    print()
    swconf = 'telnet '+ipsloc.findsw()+'\n'
    swconf += username+'\n'
    swconf += password+'\n'
    swconf += 'conf t\n'
    swconf += 'int '+ipsloc.findfrport()+'\n'
    swconf += ' description RESERVED: '+ipsloc.rrs.replace('.','-')+'-fr '+alloccode+' '+ips+'\n'
    swconf += ' switchport\n'
    swconf += ' switchport access vlan 133\n'
    swconf += ' switchport mode access\n'
    swconf += ' spanning-tree portfast edge\n'
    swconf += ' shut\n'
    swconf += '!\n'
    swconf += 'int '+ipsloc.findbkport()+'\n'
    swconf += ' description '+ipsloc.rrs.replace('.','-')+'-bk '+alloccode+'-'+ipsmgtDepth+' '+ips+' mgmt\n'
    swconf += ' switchport\n'
    swconf += ' switchport access vlan '+str(ipsmgtVlan)+'\n'
    swconf += ' switchport mode access\n'
    swconf += ' speed 100\n'
    swconf += ' duplex full\n'
    swconf += ' spanning-tree portfast edge\n'
    swconf += ' no shut\n!\n'
    swconf += ' end\n'
    print(swconf)

    ##### Generate custom cabling information:
    print()
    print('CUSTOM CABLING INFORMATION:')
    print('---------------------------')
    print()
    showIPSCabling(ips,nwdevice1,nwdevice1loc,segmentName1,deviceitf1,pnum1,1)
    showIPSCabling(ips,nwdevice2,nwdevice2loc,segmentName2,deviceitf2,pnum2,2)
    print('(NOTE: For additional custom cabling of '+nwdevice1+(' and '+nwdevice2 if nwdevice2 != nwdevice1 else '')+',')
    print('use other options of this Boreas provisioning tool.)\n\n')
    ##### Generate IPS allocation form
    input('Hit Enter to view the IPS allocation form')
    print()
    ipsform = 'IPS NETWORK INFORMATION:\n'
    ipsform += '--------------------------\n\n'
    ipsform += 'IPS ID: '+ips+'\n'
    ipsform += 'IPS Rack Location: '+ipsloc+'\n\n'
    ipsform += 'IPS Management#1 port\n\n'
    ipsform += '      connection to: '+ipsloc.findsw()+'\n'
    ipsform += '               port: '+ipsloc.findbkport()+' (Green cable)\n'
    ipsform += '          speed/dup: 100M/Full\n'
    ipsform += '   VLAN (Num/Label): '+str(ipsmgtVlan)+'/'+ipsloc.room+'r'+str("%02d" % int(ipsloc.row))+'-'+alloccode+'-'+ipsmgtDepth+'\n\n'
    ipsform += 'IPS inline port 1A\n\n'
    ipsform += '      connection to: '+nwdevice1+'\n'
    ipsform += '               port: '+deviceitf1+'\n'
    ipsform += '          speed/dup: '+speed1+'M/Full\n'
    ipsform += '         cable type: XOVER\n\n'
    ipsform += 'IPS inline port 1B\n\n'
    ipsform += '      connection to: '+nwdevice1loc.findsw()+'\n'
    ipsform += '               port: '+swport1+(' ('+nwdevice1loc+' green)' if devicePorts(nwdevice1).index(deviceitf1) == 1 else '')+'\n'
    ipsform += '          speed/dup: '+speed1+'M/Full\n'
    ipsform += '         cable type: straight-thru \n\n'
    ipsform += 'IPS inline port 2C\n\n'
    ipsform += '      connection to: '+nwdevice2+'\n'
    ipsform += '               port: '+deviceitf2+'\n'
    ipsform += '          speed/dup: '+speed2+'M/Full\n'
    ipsform += '         cable type: XOVER\n\n'
    ipsform += 'IPS inline port 2D\n\n'
    ipsform += '      connection to: '+nwdevice2loc.findsw()+'\n'
    ipsform += '               port: '+swport2+(' ('+nwdevice2loc+' green)' if devicePorts(nwdevice2).index(deviceitf2) == 1 else '')+'\n'
    ipsform += '          speed/dup: '+speed2+'M/Full\n'
    ipsform += '         cable type: straight-thru\n\n'
    ipsform += 'IPS Management\n\n'
    ipsform += '       IP: '+str(ipsmgtIPaddr.ip)+'\n'
    ipsform += '  Netmask: '+str(ipsmgtIPaddr.netmask)+'\n'
    ipsform += '  Gateway: '+str(ipsmgtIPaddr.network[1])+'\n'
    ipsform += 'Broadcast: '+str(ipsmgtIPaddr.network[-1])+'\n'
    print(ipsform)


if __name__ == '__main__':
    main()
