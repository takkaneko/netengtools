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
from hafwl2l3prov import getUPA
from hafwl2l3prov import getInterfaceIP
from hafwl2l3prov import devicePorts

def getIPS():
    """
    Prompts to enter SID/location of IPS.
    """
    while True:
        try:
            ips = input("Enter the IPS ID: ").lower().strip()
            if NWdevice(ips).is_ips():
                ips = NWdevice(ips)
                break
            else:
                print("ERROR: SERVICE ID INVALID\n")
        except AttributeError:
            print('ERROR: SERVICE ID INVALID\n')
    while True:
        try:
            ipsloc = Loccode(input("Enter the location code of "+ips+": "))
            if ipsloc.is_NWloc():
                break
            else:
                print("ERROR: INVALID LOCATION\n")
        except AttributeError:
            print("ERROR: INVALID LOCATION\n")
    return [ips,ipsloc]

def getIPSmgtInfo():
    """
    Prompts to enter IPS mgmt VLAN, depth, and IP.
    """
    # IPS mgt VLAN
    while True:
        try:
            ipsVlan = int(input('Enter the VLAN ID of IPS mgmt: '))
            if ipsVlan <= 0 or 4096 < ipsVlan:
                print('ERROR: DATA INVALID\n')
            else:
                print('OK')
                break
        except (ValueError, IndexError):
            print('ERROR: DATA INVALID\n')
    # IPS mgt depth
    while True:
        try:
            depth = input('\nEnter the depth code of the segment [0101]: ').strip() or '0101'
            if not re.match(r"^0\d{3}$",depth):
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    # IPS mgt IP
    ipsmgtIPaddr = getInterfaceIP('management interface')
    return [ipsVlan,depth,ipsmgtIPaddr]

def __sidlocMISmatch(nwdevice,deviceloc):
    """
    Helper Boolean that warns an invalid SID-LOCATION combination.
    Returns True if MISmatch is found.
    """
    return (nwdevice.is_master() and not deviceloc.is_masterloc()) or (nwdevice.is_secondary() and deviceloc.is_masterloc())

def getNWdevice(number,ipsloc):
    """
    Prompts to enter SIDs/speed/locations of a network device.
    nwdevice = newtwork device ID (firewall or loadbalancer)
    speed = 1000 or 100 (int)
    nwdeviceloc = network device location
    number: monitored device number (1 or 2) - used only in prompt messages
    """
    # Service ID
    while True:
        try:
            nwdevice = input("Enter the service ID of a monitored device #"+str(number)+": ").lower().strip()
            if NWdevice(nwdevice).is_fw() or NWdevice(nwdevice).is_lb():
                nwdevice = NWdevice(nwdevice)
                break
            else:
                print("ERROR: SERVICE ID INVALID\n")
        except AttributeError:
            print('ERROR: SERVICE ID INVALID\n')
    # Speed
    while True:
        try:
            speed = input('Enter the interface speed (Mbps)[1000]: ').strip() or '1000'
            if not re.match(r"^10{2,3}$",speed):
                print('ERROR: DATA INVALID')
            else:
                print('OK - speed = '+speed+'Mbps')
                break
        except ValueError:
            print('ERROR: DATA INVALID')
    # Location
    while True:
        try:
            nwdeviceloc = Loccode(input("Enter the location code of "+nwdevice+": "))
            if nwdeviceloc.is_NWloc() and nwdeviceloc.srr == ipsloc.srr and nwdeviceloc.rack_noa == ipsloc.rack_noa and nwdeviceloc != ipsloc:
                if __sidlocMISmatch(nwdevice,nwdeviceloc):
                    print('ERROR: ROLE MISMATCH DETECTED!\n')
                else:
                    print("OK")
                    break
            elif nwdeviceloc == ipsloc:
                print("ERROR: The "+nwdevice+" and IPS cannot take the same slot!\n")
            elif not (nwdeviceloc.srr == ipsloc.srr and nwdeviceloc.rack_noa == ipsloc.rack_noa):
                print("ERROR: The "+nwdevice+" and IPS must be in the same rack\n")
            else:
                print("ERROR: INVALID LOCATION\n")
        except AttributeError:
            print("ERROR: SYNTAX INVALID\n")
    return [nwdevice,speed,nwdeviceloc]

def getItf_and_port(nwdevice,nwdeviceloc):
    """
    Prompts to provide:
    
    1. Segment name that IPS monitors (segmentName)
    2. Device-side interface (deviceitf)
    3. Agg.switch-side switchport (swport)
    4. Also extracts the port number of the Agg.switch linecard (pnum)
    """
    # Segment Name
    segmentName = ''
    while segmentName == '':
        segmentName = input('Enter the name of the '+nwdevice+'-connected segment to monitor (e.g., DMZ): ').strip()

    # deviceitf
    while True:
        try:
            deviceitf = input('Enter the '+nwdevice+'-side INTERFACE to monitor (e.g., eth2): ').lower().strip()
            if not deviceitf in devicePorts(nwdevice):
                print('ERROR: INVALID DATA\n')
            else:
                break
        except ValueError:
            print('ERROR: INVALID DATA\n')

    # swport & pnum
    if devicePorts(nwdevice).index(deviceitf) == 1:
        swport = nwdeviceloc.findbkport()
        pnum = re.match(r"^gi(5|6)/(\d{2})$",swport).group(2)
    else:
        while True:
            try:
                swport = input('Enter the '+nwdeviceloc.findsw()+'-side switchport to monitor (e.g., gi5/33): ').lower().strip()
                mod = re.match(r"^gi(5|6)/(\d{2})$",swport).group(1)
                pnum = re.match(r"^gi(5|6)/(\d{2})$",swport).group(2)
                if 33 <= int(pnum) and int(pnum) <= 48 and nwdeviceloc.findmod() == mod:
                    break
                elif not (33 <= int(pnum) and int(pnum) <= 48):
                    print('ERROR: PORT NUMBER OUT OF RANGE\n')
                else:
                    print('ERROR: SWITCH MODULE NUMBER MISTMATCH FOUND\n')
            except (ValueError, AttributeError):
                print('ERROR: INVALID DATA\n')

    return [segmentName,deviceitf,swport,pnum]

def showCabling(ips,nwdevice,nwdeviceloc,segmentName,deviceitf,pnum,monnum):
    """
    monnum is either 1 or 2:
    
    if monnum == 1:
        IPS 1A/1B ports are used.
    if monnum ==2:
        IPS 2C/2D ports are used.
    """
    # cabling instructions
    site = nwdeviceloc.site
    if nwdeviceloc.is_masterloc(): 
        updown = 'UPPER'   
        if site == 'iad':
            bk = '50'
        else:
            bk = '43'
    else:
        updown = 'LOWER'
        if site == 'iad':
            bk = '49'
        else:
            bk = '42'
    [to_nwdevice, to_switch] = ['1A','1B'] if monnum == 1 else ['2C','2D']
    


    cabling = '\n'+segmentName+':\n'
    cabling += '  '+nwdevice+' '+deviceitf+' -> GREEN XOVER -> '+ips+'port '+to_nwdevice+'\n'
    cabling += '  '+ips+' port '+to_switch+' -> GREEN STRAIGHT -> U'+bk+' '+updown+' ORANGE PANEL p'+pnum+'\n'
    print(cabling)


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

    ##### Generate custom cabling information:
    print()
    print('CUSTOM CABLING INFORMATION:')
    print('---------------------------')
    showCabling(ips,nwdevice1,nwdevice1loc,segmentName1,deviceitf1,pnum1,1)
    showCabling(ips,nwdevice2,nwdevice2loc,segmentName2,deviceitf2,pnum2,2)
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
    ipsform += '               port: '+swport1+'\n'
    ipsform += '          speed/dup: '+speed1+'M/Full\n'
    ipsform += '         cable type: straight-thru \n\n'
    ipsform += 'IPS inline port 2C\n\n'
    ipsform += '      connection to: '+nwdevice2+'\n'
    ipsform += '               port: '+deviceitf2+'\n'
    ipsform += '          speed/dup: '+speed2+'M/Full\n'
    ipsform += '         cable type: XOVER\n\n'
    ipsform += 'IPS inline port 2D\n\n'
    ipsform += '      connection to: '+nwdevice2loc.findsw()+'\n'
    ipsform += '               port: '+swport2+'\n'
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
