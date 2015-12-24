#!/usr/bin/env python3
# hafwiloprov.py

import re
import getpass
import pexpect
from pexpect import EOF
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect
from locationcode import Loccode
from networksid import NWdevice
from ipaddress import ip_address
from ipaddress import ip_network
from ipaddress import ip_interface
from resources import getUPA
from resources import getHAdevices
from resources import getVLAN
from resources import getDepth
from resources import devicePorts

def main():
    print('WARNING: THIS OPTION SHOULD BE USED TO PROVISION A *SECNET* ILO SEGMENT ONLY')
    print('(NOT COMMON - ONLY SOME ACCENTURE ACCOUNTS HAVE THIS)\n')

    ##### Prompts to enter username, password, and allocation code:
    [username,password,alloccode] = getUPA()

    ##### Prompts to enter SIDs/speed/locations of HA pair & IPS:
    [mfw,speed,mfwloc,sfw,sfwloc,ips,ipsloc] = getHAdevices('firewall')

    print('OK\nNow let\'s define a SECNET iLO segment.\n')

    # 1. ILO VLAN:
    while True:
        try:
            iloVlan = getVLAN('SecNet iLO',[])
            if 900 <= iloVlan <= 949:
                break
            else:
                print('ERROR: ILO VLAN MUST BE BETWEEN 900 AND 949.\n')
        except AtrributeError:
            print('ERROR: AttributeError.\n')

    # 2. ILO DEPTHCODE:
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
            swpt_number = int(input('Pick the first ports on mod 4 of '+mfwloc.findsecsw()+'-'+sfwloc.findsecsw()+' that are available in pair: '))
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
    print('***************************************')
    print('Collecting switchport backup configs...')
    print('***************************************\n')
    
    for loc in [mfwloc,sfwloc]:
        try:
            child = pexpect.spawnu('telnet '+loc.findsecsw()+'.dn.net')
            child.expect('Username: ',timeout=3)
            child.sendline(username)
            child.expect('Password: ',timeout=3)
            child.sendline(password)
            child.expect('6513-'+loc.findsecsw()+'-sec-c\d{1,2}#',timeout=3)
            print(loc.findsecsw()+':\n')
            child.sendline('sh run int gi4/'+str(swpt_number))
            child.expect('6513-'+loc.findsecsw()+'-sec-c\d{1,2}#')
            print(child.before)
            child.sendline('exit')
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Unable to collect switchport configs from '+loc.findsecsw())
            print('Try collecting configs manually instead:')
            print()
            print('  '+loc.findsecsw()+':')
            print('    sh run int gi4/'+str(swpt_number))
            print()

    input('Hit Enter to view the new switchport configs.')
    print()
    # new port configs
    print('*************************************************')
    print('Use the following to apply new switchport configs')
    print('*************************************************\n')
    
    swconfigs = [(mfwloc,mfw),(sfwloc,sfw)]
    for loc,sid in swconfigs:
        swconf = 'telnet '+loc.findsecsw()+'\n'
        swconf += username+'\n'
        swconf += password+'\n'
        swconf += 'conf t\n'
        swconf += 'int gi4/'+str(swpt_number)+'\n'
        swconf += ' description '+alloccode+'-'+iloDepth+' '+sid+' back\n'
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
    print('  '+sfw+' '+fw_interface+' -> GREEN STRAIGHT -> '+sfwloc.findsecsw()+' gi4/'+str(swpt_number)+' (Direct run no patch)')
    print()
    input('Hit Enter to view the firewall allocation form')
    print()
    # HA device pair allocation form
    print('**Add the following to the firewall allocation section:\n\n')
    HAdeviceForm = 'FIREWALL NETWORK INFORMATION:\n'
    HAdeviceForm += '------------------------------\n\n'

    HAdeviceForm += '**iLO (Network '+iloDepth+'):\n\n'
    HAdeviceForm += '  Physical Interface: '+fw_interface+'\n\n'
    if mfw.findVendor() == 'cisco':
        HAdeviceForm += '  Master Firewall Back Interface: '+str(vrrp_ip)+' (gateway for servers)\n'
    else:
        HAdeviceForm += '  Firewall Back-VRRP Interface:   '+str(vrrp_ip)+' (gateway for servers)\n'
        HAdeviceForm += '  Master Firewall Back Interface: '+str(vrrp_ip+1)+'\n'
    HAdeviceForm += '  Backup Firewall Back Interface: '+str(vrrp_ip+2)+'\n\n'
    HAdeviceForm += '  Back Network:      '+str(ilonet)+'\n'
    HAdeviceForm += '  Back Netmask:      '+str(ilonet.netmask)+'\n\n'

    HAdeviceForm += '  Master Firewall Connection To (Row Agg Sw. ID): '+mfwloc.findsecsw()+'\n'
    HAdeviceForm += '  Master Firewall Connection Port:                gi4/'+str(swpt_number)+'\n\n'
    HAdeviceForm += '  Backup Firewall Connection To (Row Agg Sw. ID): '+sfwloc.findsecsw()+'\n'
    HAdeviceForm += '  Backup Firewall Connection Port:                gi4/'+str(swpt_number)+'\n\n'
    HAdeviceForm += '  SwitchPort Speed/Duplex set to:                 '+speed+'M/Full\n'
    HAdeviceForm += '   (Firewalls should be set to the same speed)\n'
    HAdeviceForm += '  SecNet Community VLAN (Num/Label):   '+str(iloVlan)+'/ilonet_'+alloccode+'\n\n'

    print(HAdeviceForm)

if __name__ == '__main__':
    main()
    
