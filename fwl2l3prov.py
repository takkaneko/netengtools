#!/usr/bin/env python3
# fwl2l3prov.py

import re
import getpass
from locationcode import Loccode
from networksid import NWdevice
from ipaddress import ip_address
from ipaddress import ip_network
from ipaddress import ip_interface
from hafwl2l3prov import getUPA
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


def getDevices(devicetype):
    """
    devicetype must be either 'firewall' or 'loadbalancer.'
    Prompts to enter SIDs/speed/locations of Stand-alone gear & IPS (w/ their error handlings).
    Only accepts the devicetype you specify.
    Returns the provided data as a list for use in main().
    
    nwdevice = newtwork device ID (firewall or loadbalancer)
    speed = 1000 or 100 (int)
    nwdeviceloc = network device location
    ips = IPS ID or 'none'
    """
    while True:
        try:
            nwdevice = input("Enter the "+devicetype+" ID: ").lower().strip()
            if NWdevice(nwdevice).is_fw_or_lb(devicetype):
                nwdevice = NWdevice(nwdevice)
                break
            else:
                print("ERROR: SERVICE ID INVALID\n")
        except AttributeError:
            print('ERROR: SERVICE ID INVALID\n')
    while devicetype == 'firewall':
        try:
            speed = input('Enter the interface speed (Mbps)[1000]: ').strip() or '1000'
            if not re.match(r"^10{2,3}$",speed):
                print('ERROR: DATA INVALID')
            else:
                print('OK - speed = '+speed+'Mbps')
                break
        except ValueError:
            print('ERROR: DATA INVALID')
    speed = speed if devicetype == 'firewall' else '1000'
    while True:
        try:
            nwdeviceloc = Loccode(input("Enter the location code of "+nwdevice+": "))
            if nwdeviceloc.is_NWloc():
                break
            else:
                print("ERROR: INVALID LOCATION FOR MASTER\n")
        except AttributeError:
            print("ERROR: INVALID LOCATION\n")
    while True:
        try:
            ips = input("Enter an IPS ID that monitors the "+devicetype+" segment(s), or type 'none': ").lower().strip().replace("'","")

            if ips == 'none' or NWdevice(ips).is_ips():
                break
            else:
                print('ERROR: INVALID SID FORMAT\n')
        except AttributeError:
            print('ERROR: SERVICE ID INVALID\n')
    if ips != 'none':
        while True:
            try:
                ipsloc = Loccode(input("Enter the location code of "+ips+": "))
                if ipsloc.is_NWloc() and (nwdeviceloc.srr == ipsloc.srr and nwdeviceloc.rack_noa == ipsloc.rack_noa) and nwdeviceloc != ipsloc:
                    print("OK")
                    break
                elif nwdeviceloc == ipsloc:
                    print("ERROR: The "+devicetype+" and IPS cannot take the same slot!\n")
                elif not (nwdeviceloc.srr == ipsloc.srr and nwdeviceloc.rack_noa == ipsloc.rack_noa):
                    print("ERROR: The "+devicetype+" and IPS must be in the same rack\n")
                else:
                    print("ERROR: INVALID LOCATION\n")
            except AttributeError:
                print("ERROR: SYNTAX INVALID\n")
    else:
        ipsloc = ''
        print("OK no IPS!")
    return [nwdevice,speed,nwdeviceloc,ips,ipsloc]

def showSummarySA(nwdevice,nwdeviceloc,IPS,IPSloc):
    if IPS != 'none':
        Devices = [[nwdevice,nwdeviceloc],
                   [IPS,IPSloc]]
    else:
        Devices = [[nwdevice,nwdeviceloc]]
    output = '\n'
    output += 'The standard front/back switchports of the devices that you entered:\n\n'
    for sid,loc in Devices:
        output += sid+' ('+loc+'):\n'
        output += ' Front: '+loc.findsw()+' '+loc.findfrport()+'\n'
        output += ' Back:  '+loc.findsw()+' '+loc.findbkport()+'\n\n'
    print(output)

def main():
    ##### Prompts to enter username, password, and allocation code:
    [username,password,alloccode] = getUPA()

    ##### Prompts to enter SIDs/speed/locations of HA pair & IPS:
    [mfw,speed,mfwloc,ips,ipsloc] = getDevices('firewall')

    ###### Summary Output of Devices:
    showSummarySA(mfw,mfwloc,ips,ipsloc)

    ###### Prompts to select a sync port:
    availPorts = devicePorts(mfw)
    
    ###### FRONT SEGMENT
    # 1. VLAN:
    Vlans = [] # FW vlans. ipsmgtVlan will not be included.
    frontVlan = getVLAN('the firewall front',Vlans)
    Vlans.append(frontVlan)

    # 2. DEPTHCODE:
    Depths = []
    frontdepth = getDepth('firewall','0001',Depths)
    Depths.append(frontdepth)

    # 3. SUBNETS:
    frontnet = getSubnets('the firewall front')

    print('OK\nNow let\'s define firewall back segments, one by one.\n')

    ###### STANDARD BACK SEGMENT
    # 1. NAME:
    Segments = ['front']  # FW segment names
    SegmentsL = ['front'] # FW segment names with all chars lowered, for uniqueness checks.
    backName = getUniqueSegmentName(SegmentsL)
    Segments.append(backName)
    SegmentsL.append(backName.lower())

    # 2. VLAN:
    backVlan = getVLAN(backName,Vlans)
    Vlans.append(backVlan)

    # 3. DEPTHCODE:
    backdepth = getDepth('firewall','0101',Depths)
    Depths.append(backdepth)

    # 4. SUBNETS:
    backnets = getSubnets(backName)

    # 5. IPS QUESTION:
    monitored = 0
    Sniff = ['n']
    [monitored,Sniff] = askifMonitor(ips,monitored,Sniff)

    Ports = [1,16]  # FW segment ports. First two for front & back (1,16) are fake.
    SubnetLists = [frontnet,backnets]
    ###### 'ADD?' ######
    add_more_segment = addQuestion()
    
    #################### LOOP - BACK SEGMENTS ADDITIONS ########################
    while add_more_segment == 'y':

        ###### CHOOSE AUX PORT ######
        auxport = pickPort(mfwloc,Ports)
        Ports.append(auxport)

        ###### CREATE SEGMENT NAME ######
        auxsegment = getUniqueSegmentName(SegmentsL)
        Segments.append(auxsegment)
        SegmentsL.append(auxsegment.lower())

        ###### CHOOSE VLAN ######
        auxvlan = getVLAN(auxsegment,Vlans)
        Vlans.append(auxvlan)

        ###### CHOOSE DEPTH CODE ######
        auxdepth = getDepth('firewall','0102',Depths)
        Depths.append(auxdepth)

        ###### CHOOSE SUBNETS ######
        SubnetLists.append(getSubnets(auxsegment))

        ###### IPS OPTION ######
        [monitored,Sniff] = askifMonitor(ips,monitored,Sniff)

        ###### 'ADD?' ######
        add_more_segment = addQuestion()

    ############################## END OF LOOP #################################
    ###### IPS MANAGEMENT
    if ips != 'none':
        # 1. VLAN:
        print('\nNow choose the IPS management VLAN.\n'
              +'It can be any one of the VLANs that you allocated to this customer.\n'
              +'However, try avoiding a VLAN that is widely exposed to the Internet.')
        ipsmgtVlan = getIpsVLAN('firewall',frontVlan)

        # 2. DEPTH CODE:
        ipsmgtDepth = getIPSDepth(Vlans,ipsmgtVlan,Depths)
    
        # 3. IP ADDRESS:
        ipsmgtIPaddr = getInterfaceIP('the IPS management')

    #############################################################################
    print('\nThe rest will generate port configs, custom cabling info, allocation form, etc.\n')
    
    # back up port configs
    print('******************************************************')
    print('Use the following to collect switchport backup configs')
    print('******************************************************\n')
    
    backup = 'telnet '+mfwloc.findsw()+'\n'
    backup += username+'\n'
    backup += password+'\n'
    backup += 'sh run int '+mfwloc.findfrport()+'\n'
    backup += 'sh run int '+mfwloc.findbkport()+'\n'
    for port in Ports[2:]:
        backup += 'sh run int gi'+mfwloc.findmod()+'/'+str(port)+'\n'
    if ips != 'none':
        if mfwloc.findmod() != ipsloc.findmod():
            backup += 'exit\n\n'
            backup += 'telnet '+ipsloc.findsw()+'\n'
            backup += username+'\n'
            backup += password+'\n'
        backup += 'sh run int '+ipsloc.findfrport()+'\n'
        backup += 'sh run int '+ipsloc.findbkport()+'\n'
        backup += 'exit\n'
    else:
        backup += 'exit\n'
    print(backup)
    input('Hit Enter to view the new switchport configs.')
    print()
    # new port configs
    print('*************************************************')
    print('Use the following to apply new switchport configs')
    print('*************************************************\n')
    
    swconf = 'telnet '+mfwloc.findsw()+'\n'
    swconf += username+'\n'
    swconf += password+'\n'
    swconf += 'conf t\n'
    swconf += 'int '+mfwloc.findfrport()+'\n'
    swconf += ' description '+mfwloc.rrs.replace('.','-')+'-fr '+alloccode+'-'+Depths[0]+' '+mfw+' front\n'
    swconf += ' switchport\n'
    swconf += ' switchport access vlan '+str(Vlans[0])+'\n'
    swconf += ' switchport mode access\n'
    swconf += ' speed 1000\n'
    swconf += ' duplex full\n'
    swconf += ' spanning-tree portfast edge\n'
    swconf += ' no shut\n'
    swconf += '!\n'
    swconf += 'int '+mfwloc.findbkport()+'\n'
    swconf += ' description '+mfwloc.rrs.replace('.','-')+'-bk '+alloccode+'-'+Depths[1]+' '+mfw+' back\n'
    swconf += ' switchport\n'
    swconf += ' switchport access vlan '+str(Vlans[1])+'\n'
    swconf += ' switchport mode access\n'
    swconf += ' speed 1000\n'
    swconf += ' duplex full\n'
    swconf += ' spanning-tree portfast edge\n'
    swconf += ' no shut\n'
    swconf += '!\n'
    aux = 2
    for port in Ports[2:]:
        swconf += 'int gi'+mfwloc.findmod()+'/'+str(port)+'\n'
        swconf += ' description '+mfwloc.rrs.replace('.','-')+'-b'+str(aux)+' '+alloccode+'-'+Depths[aux]+' '+mfw+' back'+str(aux)+'\n'
        swconf += ' switchport\n'
        swconf += ' switchport access vlan '+str(Vlans[aux])+'\n'
        swconf += ' switchport mode access\n'
        swconf += ' speed 1000\n'
        swconf += ' duplex full\n'
        swconf += ' spanning-tree portfast edge\n'
        swconf += ' no shut\n'
        swconf += '!\n'
        aux += 1
    if ips != 'none':
        if mfwloc.findmod() != ipsloc.findmod():
            swconf += 'exit\n\n'
            swconf += 'telnet '+ipsloc.findsw()+'\n'
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
        swconf += ' spanning-tree portfast edge\n'
        swconf += ' no shut\n!\n'
        swconf += ' end\n'
    else:
        swconf += ' end\n'
    print(swconf)

    input('Hit Enter to view the custom cabling information')
    print()
    # cabling instructions
    site = mfwloc.site
    rs = mfwloc.rs
    if site == 'iad':
        nw_rs = ('3.1','3.2','3.3','3.4','3.5','3.6','3.7','3.8',
                 '3.9','3a.9','3.10','3a.10','3.11','3a.11','3.12','3a.12',
                 '3.13','3a.13','3.14','3a.14','3.15','3a.15','3.16','3a.16',
                 '3.17','3a.17','3.18','3a.18','3.19','3a.19','3.20','3a.20',
                 '12.1','12.2','12.3','12.4','12.5','12.6','12.7','12.8',
                 '12.9','12a.9','12.10','12a.10','12.11','12a.11','12.12','12a.12',
                 '12.13','12a.13','12.14','12a.14','12.15','12a.15','12.16','12a.16',
                 '12.17','12a.17','12.18','12a.18','12.19','12a.19','12.20','12a.20')
    else:
        nw_rs = ('3.1', '3a.1', '3.2', '3a.2', '3.3', '3a.3', '3.4', '3a.4', 
                 '3.5', '3a.5', '3.6', '3a.6', '3.7', '3a.7', '3.8', '3a.8',
                 '3.9', '3a.9', '3.10', '3a.10', '3.11', '3a.11', '3.12', '3a.12',
                 '3.13', '3a.13', '3.14', '3a.14', '3.15', '3a.15', '3.16', '3a.16',
                 '22.1', '22a.1', '22.2', '22a.2', '22.3', '22a.3', '22.4', '22a.4',
                 '22.5', '22a.5', '22.6', '22a.6', '22.7', '22a.7', '22.8', '22a.8',
                 '22.9', '22a.9', '22.10', '22a.10', '22.11', '22a.11', '22.12', '22a.12',
                 '22.13', '22a.13', '22.14', '22a.14', '22.15', '22a.15', '22.16', '22a.16')

    if mfwloc.is_masterloc(): 
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
    print('CUSTOM CABLING INFORMATION:')
    print('---------------------------\n')
    cabling = ''
    cumulative = 0
    if Sniff[1] == 'y':
        cumulative += 1
        cabling += backName+':\n'
        cabling += '  '+mfw+' '+availPorts[1]+' -> GREEN XOVER -> '+ips+'port 1A\n'
        cabling += '  '+ips+' port 1B -> GREEN STRAIGHT -> U'+bk+' '+updown+' ORANGE PANEL p'+str(nw_rs.index(rs)%32+1)+'\n\n'
    auxII = 2
    for segment in Segments[2:]:
        cabling += segment+':\n'
        if Sniff[auxII] == 'y':
            cumulative += 1
            cabling += '  '+mfw+' '+availPorts[auxII]+' -> GREEN XOVER -> '+ips+' port '+str('1A' if cumulative == 1 else '2C')+'\n'
            cabling += '  '+ips+' port '+str('1B' if cumulative == 1 else '2D')+' -> GREEN STRAIGHT -> U'+bk+' '+updown+' ORANGE PANEL p'+str(Ports[auxII])+'\n\n'
        else:
            cabling += '  '+mfw+' '+availPorts[auxII]+' -> GREEN STRAIGHT -> U'+bk+' '+updown+' ORANGE PANEL p'+str(Ports[auxII])+'\n\n'
        auxII += 1
    print(cabling)
    input('Hit Enter to view the firewall allocation form')
    print()
    # HA device pair allocation form
    if mfw.is_fw():
        devicetype = 'firewall'
    else:
        devicetype = 'loadbalancer'
    deviceForm = devicetype.upper()+' NETWORK INFORMATION:\n'
    deviceForm += '------------------------------\n\n'
    deviceForm += 'Allocation Code: '+alloccode+'\n\n'
    deviceForm += devicetype.title()+' ID:            '+mfw+'\n'
    deviceForm += 'Rack/Console Loc.Code:  '+mfwloc+'\n'
    deviceForm += devicetype.title()+' Network Unit: Infra 4.0, equipment rack: '+mfwloc.row+'-'+mfwloc.rack_noa+'\n\n'
    deviceForm += devicetype.title()+'s Front (Network '+frontdepth+')\n\n'
    deviceForm += '  Physical Interface: '+availPorts[0]+'\n\n'
    deviceForm += '  Front Interface:  '+str(frontnet[0][4])+'\n'
    deviceForm += '  Default Gateway:  '+str(frontnet[0][1])+'\n'
    deviceForm += '  Front Network:    '+str(frontnet[0])+'\n'
    deviceForm += '  Front Netmask:    '+str(frontnet[0].netmask)+'\n\n'
    deviceForm += '  Connection To:    '+mfwloc.findsw()+'\n'
    deviceForm += '  Connection Port:  '+mfwloc.findfrport()+'\n\n'
    deviceForm += '  SwitchPort Speed/Duplex set to: '+speed+'M/Full\n'
    deviceForm += '   ('+devicetype.title()+'s should be set to the same speed)\n'
    deviceForm += '  INFRA4.0 VLAN (Num/Label):   '+str(frontVlan)+'/'+mfwloc.room+'r'+str("%02d" % int(mfwloc.row))+'-'+alloccode+'-'+frontdepth+'\n\n'
    deviceForm += devicetype.title()+'s Backs:\n\n'
    deviceForm += '**'+backName+' (Network '+backdepth+')\n\n'
    deviceForm += '  Physical Interface: '+availPorts[1]+'\n\n'
    deviceForm += '  Back Interface:   '+str(backnets[0][1])+' (gateway for ???)\n'
    deviceForm += '  Back Network:     '+str(backnets[0])+'\n'
    deviceForm += '  Back Netmask:     '+str(backnets[0].netmask)+'\n\n'
    ####################### ADD LOOP FOR ADDITIONAL ALIASES #######################
    if len(backnets) > 1:
        for backnet in backnets[1:]:
            deviceForm += ' *Add\'tl Alias for '+backName+':\n\n'
            deviceForm += '  Back Interface:   '+str(backnet[1])+' (gateway for ???)\n'
            deviceForm += '  Back Network:     '+str(backnet)+'\n'
            deviceForm += '  Back Netmask:     '+str(backnet.netmask)+'\n\n'
    ###############################################################################
    deviceForm += '  Connection To:    '+mfwloc.findsw()+'\n'
    deviceForm += '  Connection Port:  '+mfwloc.findbkport()+'\n\n'
    deviceForm += '  SwitchPort Speed/Duplex set to: '+speed+'M/Full\n'
    deviceForm += '   ('+devicetype.title()+'s should be set to the same speed)\n'
    deviceForm += '  INFRA4.0 VLAN (Num/Label):   '+str(backVlan)+'/'+mfwloc.room+'r'+str("%02d" % int(mfwloc.row))+'-'+alloccode+'-'+backdepth+'\n\n'
    auxIII = 2
    for segment in Segments[2:]:
        deviceForm += '**'+segment+' (Network '+Depths[auxIII]+')\n\n'
        deviceForm += '  Physical Interface: '+availPorts[auxIII]+'\n\n'
        deviceForm += '  Back Interface:   '+str(SubnetLists[auxIII][0][1])+' (gateway for ???)\n'
        deviceForm += '  Back Network:     '+str(SubnetLists[auxIII][0])+'\n'
        deviceForm += '  Back Netmask:     '+str(SubnetLists[auxIII][0].netmask)+'\n\n'
        ####################### ADD LOOP FOR ADDITIONAL ALIASES #######################
        if len(SubnetLists[auxIII]) > 1:
            for aliasnet in SubnetLists[auxIII][1:]:
                deviceForm += ' *Add\'tl Alias for '+Segments[auxIII]+':\n\n'
                deviceForm += '  Back Interface:   '+str(aliasnet[1])+' (gateway for ???)\n'
                deviceForm += '  Back Network:     '+str(aliasnet)+'\n'
                deviceForm += '  Back Netmask:     '+str(aliasnet.netmask)+'\n\n'
        ###############################################################################
        deviceForm += '  Connection To:    '+mfwloc.findsw()+'\n'
        deviceForm += '  Connection Port:  gi'+mfwloc.findmod()+'/'+str(Ports[auxIII])+'\n\n'
        deviceForm += '  SwitchPorts Speed/Duplex set to: '+speed+'M/Full\n'
        deviceForm += '   ('+devicetype.title()+'s should be set to the same speed)\n'
        deviceForm += '  INFRA4.0 VLAN (Num/Label):   '+str(Vlans[auxIII])+'/'+mfwloc.room+'r'+str("%02d" % int(mfwloc.row))+'-'+alloccode+'-'+Depths[auxIII]+'\n\n'
        auxIII += 1
    print(deviceForm)
    if ips != 'none':
        input('Hit Enter to view the IPS allocation form')
        print()
        # [IF APPLICABLE] IPS allocation form
        ipsform = 'IPS NETWORK INFORMATION:\n'
        ipsform += '--------------------------\n\n'
        ipsform += 'IPS ID: '+ips+'\n'
        ipsform += 'IPS Rack Location: '+ipsloc+'\n\n'
        ipsform += 'IPS Management#1 port\n\n'
        ipsform += '      connection to: '+ipsloc.findsw()+'\n'
        ipsform += '               port: '+ipsloc.findbkport()+' (Green cable)\n'
        ipsform += '          speed/dup: 100M/Full\n'
        ipsform += '   VLAN (Num/Label): '+str(ipsmgtVlan)+'/'+ipsloc.room+'r'+str("%02d" % int(ipsloc.row))+'-'+alloccode+'-'+ipsmgtDepth+'\n\n'
        if Sniff[1] == 'y':
            ipsform += 'IPS inline port 1A\n\n'
            ipsform += '      connection to: '+mfw+'\n'
            ipsform += '               port: '+availPorts[1]+'\n'
            ipsform += '          speed/dup: '+speed+'M/Full\n'
            ipsform += '         cable type: XOVER\n\n'
            ipsform += 'IPS inline port 1B\n\n'
            ipsform += '      connection to: '+ipsloc.findsw()+'\n'
            ipsform += '               port: '+mfwloc.findbkport()+' ('+mfwloc+' green)\n'
            ipsform += '          speed/dup: '+speed+'M/Full\n'
            ipsform += '         cable type: straight-thru \n\n'
            auxIV = 2
            for sniff in Sniff[2:]:
                if sniff == 'y':
                    ipsform += 'IPS inline port 2C\n\n'
                    ipsform += '      connection to: '+mfw+'\n'
                    ipsform += '               port: '+availPorts[auxIV]+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: XOVER\n\n'
                    ipsform += 'IPS inline port 2D\n\n'
                    ipsform += '      connection to: '+ipsloc.findsw()+'\n'
                    ipsform += '               port: gi'+ipsloc.findmod()+'/'+str(Ports[auxIV])+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: straight-thru\n\n'
                    auxIV += 1
                else:
                    auxIV += 1
        else:
            auxV = 0
            auxVI = 2
            for sniff in Sniff[2:]:
                if sniff == 'y':
                    ipsform += 'IPS inline port '+('1A' if auxV == 0 else '2C')+'\n\n'
                    ipsform += '      connection to: '+mfw+'\n'
                    ipsform += '               port: '+availPorts[auxVI]+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: XOVER\n\n'
                    ipsform += 'IPS inline port '+('1B' if auxV == 0 else '2D')+'\n\n'
                    ipsform += '      connection to: '+ipsloc.findsw()+'\n'
                    ipsform += '               port: gi'+ipsloc.findmod()+'/'+str(Ports[auxVI])+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: straight-thru\n\n'
                    auxV += 1
                    auxVI += 1
                else:
                    auxVI += 1
        ipsform += 'IPS Management\n\n'
        ipsform += '       IP: '+str(ipsmgtIPaddr.ip)+'\n'
        ipsform += '  Netmask: '+str(ipsmgtIPaddr.netmask)+'\n'
        ipsform += '  Gateway: '+str(ipsmgtIPaddr.network[1])+'\n'
        ipsform += 'Broadcast: '+str(ipsmgtIPaddr.network[-1])+'\n'
        print(ipsform)

if __name__ == '__main__':
    main()
    
