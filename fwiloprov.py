#!/usr/bin/env python3
# hafwiloprov.py

import re
import getpass
from locationcode import Loccode
from networksid import NWdevice
from ipaddress import ip_address
from ipaddress import ip_network
from ipaddress import ip_interface
from hafwl2l3prov import getUPA
from hafwl2l3prov import  getHAdevices
from fwl2l3prov import getDevices
from hafwl2l3prov import  showSummary
from fwl2l3prov import showSummarySA
from hafwl2l3prov import  getVLAN
from hafwl2l3prov import  getIpsVLAN
from hafwl2l3prov import  getDepth
from hafwl2l3prov import  getIPSDepth
from hafwl2l3prov import  remdup
from hafwl2l3prov import  getSubnets
from hafwl2l3prov import  getUniqueSegmentName
from hafwl2l3prov import  askifMonitor
from hafwl2l3prov import  addQuestion
from hafwl2l3prov import  pickPort
from hafwl2l3prov import  getInterfaceIP
from hafwl2l3prov import  devicePorts
from hafwl2l3prov import  defaultsync
from hafwl2l3prov import  chooseSyncInt

def main():
    print('WARNING: THIS OPTION SHOULD BE USED TO PROVISION A *SECNET* ILO SEGMENT')
    print('(NOT COMMON - ONLY SOME ACCENTURE ACCOUNTS HAVE THIS)\n')

    ##### Prompts to enter username, password, and allocation code:
    [username,password,alloccode] = getUPA()

    ##### Prompts to enter SIDs/speed/locations
    [mfw,speed,mfwloc,ips,ipsloc] = getDevices('firewall')

    print('OK\nNow let\'s define a SECNET iLO segment.\n')

    ###### STANDARD BACK SEGMENT
    # 1. VLAN:
    while True:
        try:
            iloVlan = getVLAN('SecNet iLO',[])
            if 900 <= iloVlan <= 949:
                break
            else:
                print('ERROR: ILO VLAN MUST BE BETWEEN 900 AND 949.\n')
        except AtrributeError:
            print('ERROR: AttributeError.\n')

    # 2. DEPTHCODE:
    iloDepth = getDepth('firewall','9901',[])

    # 3. ILO SUBNET:
    if mfwloc.site == 'iad':
        ilonet = ip_network('10.176.0.0/16')
    else:
        ilonet = ip_network('10.177.0.0/16')

    # 4. FIREWALL INTERFACE:
    while True:
        try:
            fw_interface = input('Enter the firewall interface for the iLO segment (e.g, eth1, s1p1, gi0/4, etc.): ').strip()
            if fw_interface in devicePorts(mfw):
                break
            else:
                print('ERROR: INVALID INTERFACE\n')
        except AttributeError:
            print('ERROR: INVALID INTERFACE\n')

    # 5. SWITCHPORT NUMBER:
    while True:
        try:
            swpt_number = int(input('Pick the first available port on mod 4 of '+mfwloc.findsecsw()+': '))
            if 1 <= swpt_number <= 48:
                break
            else:
                print('ERROR: NUMBER OUT OF RANGE\n')
        except (AttributeError,ValueError):
            print('ERROR: INVALID DATA\n')
    
    # 6. VRRP IP:
    while True:
        try:
            vrrp_ip = ip_address(input('Enter the IP address of the iLO gateway/VRRP interface (e.g., 10.176.128.9): '))
            if vrrp_ip in ilonet:
                break
            else:
                print('ERROR: '+str(vrrp_ip)+' does not belong to '+str(ilonet)+'.\n')
        except ValueError:
            print('ERROR: INVALID ADDRESS/NETMASK\n')


    #############################################################################
    print('\nThe rest will generate port configs, custom cabling info, allocation form, etc.\n')
    
    # back up port configs
    print('******************************************************')
    print('Use the following to collect switchport backup configs')
    print('******************************************************\n')
    
    backup = 'telnet '+mfwloc.findsecsw()+'\n'
    backup += username+'\n'
    backup += password+'\n'
    backup += 'sh run int gi4/'+str(swpt_number)+'\n'
    backup += 'exit\n'
    print(backup)
    input('Hit Enter to view the new switchport configs.')
    print()
    # new port configs
    print('*************************************************')
    print('Use the following to apply new switchport configs')
    print('*************************************************\n')
    
    swconf = 'telnet '+mfwloc.findsecsw()+'\n'
    swconf += username+'\n'
    swconf += password+'\n'
    swconf += 'conf t\n'
    swconf += 'int gi4/'+str(swpt_number)+'\n'
    swconf += ' description '+alloccode+'-'+iloDepth+' '+mfw+' back\n'
    swconf += ' switchport\n'
    swconf += ' switchport access vlan '+str(iloVlan)+'\n'
    swconf += ' switchport private-vlan host-association 11 '+str(iloVlan)+'\n'
    swconf += ' switchport mode private-vlan host\n'
    swconf += ' speed '+speed+'\n'
    swconf += ' duplex full\n'
    swconf += ' spanning-tree portfast edge\n'
    swconf += ' no shut\n'
    swconf += ' end\n'
    print(swconf)
    input('Hit Enter to view the custom cabling information')
    print()
    # cabling instructions
    print('CUSTOM CABLING INFORMATION:')
    print('---------------------------\n')
    print()
    print('iLO:')
    print('  '+mfw+' '+fw_interface+' -> GREEN STRAIGHT -> '+mfwloc.findsecsw()+' gi4/'+str(swpt_number)+' (Direct run no patch)')
    print()
    input('Hit Enter to view the firewall allocation form')
    print()
    # Firewall allocation form
    print('**Add the following to the firewall allocation section:\n\n')
    HAdeviceForm = 'FIREWALL NETWORK INFORMATION:\n'
    HAdeviceForm += '------------------------------\n\n'

    HAdeviceForm += '**iLO (Network '+iloDepth+'):\n\n'
    
    HAdeviceForm += '  Physical Interface: '+fw_interface+'\n\n'
    
    HAdeviceForm += '  Back Interface:   '+str(vrrp_ip)+' (gateway for servers)\n'
    HAdeviceForm += '  Back Network:     '+str(ilonet)+'\n'
    HAdeviceForm += '  Back Netmask:     '+str(ilonet.netmask)+'\n\n'

    HAdeviceForm += '  Connection To:    '+mfwloc.findsecsw()+'\n'
    HAdeviceForm += '  Connection Port:  gi4/'+str(swpt_number)+'\n\n'

    HAdeviceForm += '  SwitchPort Speed/Duplex set to: '+speed+'M/Full\n'
    HAdeviceForm += '   (Firewalls should be set to the same speed)\n'
    HAdeviceForm += '  SecNet VLAN (Num/Label):   '+str(iloVlan)+'/ilonet_'+alloccode+'\n\n'

    print(HAdeviceForm)

if __name__ == '__main__':
    main()
    
