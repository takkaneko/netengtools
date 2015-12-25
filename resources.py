#!/usr/bin/env python3
# resourcesha.py

import re
import getpass
from locationcode import Loccode
from networksid import NWdevice
from ipaddress import ip_address
from ipaddress import ip_network
from ipaddress import ip_interface
import pexpect
from pexpect import EOF
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect

#####THE FOLLOWING FUNCTIONS ARE USED IN BOTH HA & NON-HA PROVISIONING SCRIPTS#####

# getUPA
# getVLAN
# getIpsVLAN
# getDepth
# getIPSDepth
# getSubnets
# getUniqueSegmentName
# askifMonitor
# addQuestion
# pickPort
# getInterfaceIP
# devicePorts
# defaultsync
# chooseSyncInt
# makeSVI

def getUPA():
    """
    UPA stands for: username/password/allocation code.
    Prompts to enter these information.
    """
    #import getpass
    username = ''
    while username == '':
        username = input("Enter your tacacs username: ")
    password = ''
    while password == '':
        password = getpass.getpass(prompt='Enter your tacacs password: ',stream=None)
    print('OK')
    alloccode = ''
    while alloccode == '':
        alloccode = input('Enter an allocation code: ').lower().strip()
    print('OK')
    
    return [username,password,alloccode]

def getVLAN(segment,Vlans):
    while True:
        try:
            vlan = int(input('Enter the VLAN ID of '+segment+': '))
            if vlan in Vlans:
                print('ERROR: The selected VLAN is already taken!\n')
            elif vlan <= 0 or 4096 < vlan:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return vlan

def getIpsVLAN(devicetype,unprotectedVlan):
    """
    Returns an IPS management VLAN, trying to avoid potentially an unprotected VLAN.
    devicetype is either 'firewall' or loadbalancer'
    """
    while True:
        try:
            ipsVlan = int(input('Enter the VLAN ID of IPS mgmt: '))
            if ipsVlan == unprotectedVlan:
                print('WARNING: '+devicetype.upper()+' FRONT VLAN MAY BE EXPOSED TO THE INTERNET!\n')
                ans = input('ARE YOU SURE TO PROCEED? [y/N]: ').lower().strip()
                if ans[0] == 'y':
                    print('OK - IPS mgmt VLAN is set to '+str(ipsVlan))
                    break
                elif ans[0] == 'n' or ans[0] == '':
                    pass
                else:
                    print('ERROR: INVALID ANSWER\n')
            elif ipsVlan <= 0 or 4096 < ipsVlan:
                print('ERROR: DATA INVALID\n')
            else:
                print('OK')
                break
        except (ValueError, IndexError):
            print('ERROR: DATA INVALID\n')
    return ipsVlan

def getDepth(devicetype,default,Depths):
    #import re
    while True:
        try:
            depth = input('\nEnter the depth code of this '+devicetype+' segment ['+default+']: ').strip() or default
            if not re.match(r"^\d{4}$",depth):
                print('ERROR: DATA INVALID\n')
            elif depth in Depths:
                print('ERROR: The depth code already exists!\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return depth

def getIPSDepth(Vlans,ipsmgtVlan,Depths):
    if ipsmgtVlan in Vlans:
        idx = Vlans.index(ipsmgtVlan)
        return Depths[idx]
    else:
        return getDepth('IPS management','0101',Depths)

def getSubnets(segment,nwdevice):
    def remdup(List):
        """
        Removes duplicate entries from List: 
    
        >>> list
        [1, 2, 3, 4, 5, 7, 4, 2, 4, 6, 3, 1]
        >>> remdup(List)
        [1, 2, 3, 4, 5, 7, 6]
        """
        List2 = []
        for i in List:
            if i not in List2:
                List2.append(i)
        return List2
    #import re
    #from ipaddress import ip_network
    while True:
        try:
            nets = input('Enter a subnet '+('or subnets separated by commas ' if nwdevice.findVendor() != 'cisco' else '' )+'for '+segment+': ')
            subnets = re.findall(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})",nets)
            subnets = remdup(subnets) # Removes duplicate entries
            if nwdevice.findVendor() == 'cisco' and len(subnets)>1:
                subnets = [subnets[0]]
                print('WARNING: Cisco gear accepts a single subnet. Only the first subnet was accepted.\n')
            if subnets != []:
                for i,_ in enumerate(subnets):
                    subnets[i] = ip_network(subnets[i])
                break
            else:
                pass
        except ValueError:
            print('ERROR: INVALID ADDRESS/NETMASK FOUND\n')
    return subnets

def getUniqueSegmentName(List):
    """
    Evaluates uniqueness of a lower-cased input (segmentName.lower()) against List.
    Returns the input segmentName once uniqueness is validated.
    """
    while True:
        try:
            segmentName = input('Enter the friendly name of this segment: ').strip()
            if segmentName.lower() in List:
                print('ERROR: '+segmentName+' already exists!\n')
            elif segmentName == '':
                print('ERROR: DATA INVALID\n') 
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return segmentName

def askifMonitor(ips,monitored,Sniff):
    while ips != 'none' and monitored < 2:
        try:
            answer = input('Monitored by IPS? [y/N]: ').lower().strip()
            if answer[0] == 'y':
                monitored += 1
                Sniff.append('y')
                print('OK - Set to be monitored by IPS!')
                break
            elif answer[0] == 'n':
                Sniff.append('n')
                print('OK')
                break
            else:
                print('ERROR: INVALID ANSWER\n')
        except IndexError:
            print('ERROR: DATA INVALID\n')
    if ips == 'none' or monitored == 2:
        Sniff.append('n')
    return [monitored,Sniff]

def addQuestion():
    add = input('Add an additional back segment? [y/N]: ').lower().strip()
    while True:
        try:
            if add[0] == 'y':
                break
            elif add[0] == 'n':
                print('OK - no additional segment')
                break
            else:
                print('ERROR: INVALID ANSWER\n')
                add = input('Add an additional back segment? [y/N]: ').lower().strip()
        except IndexError:
            print('ERROR: INVALID ANSWER\n')
            add = input('Add an additional back segment? [y/N]: ').lower().strip()
    return add[0]

def pickPort(loc,PortList):
    """
    Evaluates availability of an input (xport) against PortList.
    Returns xport once it is verified to be available.
    """
    #from locationcode import Loccode
    while True:
        try:
            xport = int(input('Pick the next available port number (>=33) on mod '
                                +loc.findmod()+' of '+loc.findsw()+'-'+loc.peerloc().findsw()+': '))
            if not 33 <= xport <= 48:
                print('ERROR: INVALID PORT NUMBER\n')
            elif xport in PortList:
                print('ERROR: The selected port number is already taken!\n')
            else:
                print('OK')
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return xport

def getInterfaceIP(interfaceName):
    #from ipaddress import ip_interface
    while True:
        try:
            interfaceIP = ip_interface(input('Enter an IP address of '+interfaceName+' (e.g., 192.168.0.5/28): '))
            break
        except ValueError:
            print('ERROR: INVALID ADDRESS/NETMASK\n')
    return interfaceIP

def devicePorts(sid):
    #from networksid import NWdevice
    asa85Ports = ['gi0/0','gi0/1','gi0/2','gi0/3','gi0/4','gi0/5', # for standard network segments or sync
                  'gi1/0','gi1/1','gi1/2','gi1/3','gi1/4','gi1/5', # for standard network segments or sync
                  'gi0/6','gi0/7','gi0/8','gi0/9', # 10G ports for possible sync
                  'gi1/6','gi1/7','gi1/8','gi1/9'] # 10G ports for possible sync
    asa25or50Ports = ['gi0/0','gi0/1','gi0/2','gi0/3','gi0/4','gi0/5','gi0/6','gi0/7'] 
    asa10Ports = ['gi0/0','gi0/1','gi0/2','gi0/3','gi0/4','gi0/5']
    nokia3XXPorts = ['eth1','eth2','eth3','eth4',
                     's1p1','s1p2','s1p3','s1p4',
                     's2p1','s2p2','s2p3','s2p4'] 
    UTM130Ports = ['EXT(5)','INT(1)','LAN1(2)','LAN2(3)','DMZ(4)']
    nokia12000Ports = ['eth1','eth2','eth3','eth4','eth5','eth6','eth7','eth8',
                       's1p1','s1p2','s1p3','s1p4','s1p5','s1p6','s1p7','s1p8']
    nokia4400Ports = ['eth1','eth2','eth3','eth4','eth5','eth6','eth7','eth8']
    nokia2200Ports = ['eth1','eth2','eth3','eth4','eth5','eth6']
    alteonPorts = ['p1','p2','p3','p4','p5','p7','p8']
    genericPorts = ['p1','p2','p3','p4','p5','p6','p7','p8','p9','p10']
    if sid.model == 'asa85':
        return asa85Ports
    elif sid.model in ['asa25','asa50']:
        return asa25or50Ports
    elif sid.model == 'asa10':
        return asa10Ports
    elif sid.model == 'alteon':
        return alteonPorts
    elif sid.model == 'chkp13':
        return UTM130Ports
    elif sid.model == 'chkp40':
        return nokia4400Ports
    elif sid.model in ['chkp20','nokia29']:
        return nokia2200Ports
    elif sid.model in ['nokia39','nokia56']:
        return nokia3XXPorts
    elif sid.model == 'chkp120':
        return nokia12000Ports
    else:
        return genericPorts

def defaultsync(sid):
    """
    sid must be an HA-capable device
    """
    #from networksid import NWdevice
    if sid.model == 'asa85':
        return 'gi1/5'
    elif sid.model in ['asa25','asa50']:
        return 'gi0/7'
    elif sid.model == 'asa10':
        return 'gi0/5'
    elif sid.model == 'alteon':
        return 'none'
    elif sid.model in ['chkp40','chkp120']:
        return 'eth8'
    elif sid.model in ['chkp20','nokia29']:
        return 'eth6'
    elif sid.model in ['nokia39','nokia56']:
        return 'eth4'
    else:
        return 'p10'

def chooseSyncInt(sid):
    #from networksid import NWdevice
    while True:
        try:
            syncinterface = input('Enter a sync interface, or type \'none\' ['+defaultsync(sid)+']: ').lower().strip() or defaultsync(sid)
            if syncinterface in devicePorts(sid) or syncinterface == 'none':
                break
            else:
                print('ERROR: INVALID DATA\n')
        except ValueError:
            print('ERROR: INVALID DATA\n')
    return syncinterface

def makeSVI(username,password,mfwloc,frontVlan,alloccode,frontnets):
    """
    Relevant only if a root 0001 is present. 
    Therefore, makeSVI should always follow an if statement such as:
    
    if frontdepth == '0001':
    """
    input('Hit Enter to collect SVI backup scripts.')
    print()
    #import pexpect
    #from pexpect import EOF
    #from pexpect import TIMEOUT
    #from pexpect import ExceptionPexpect
    #from locationcode import Loccode
    # backup SVI configs
    print('********************************')
    print('Collecting SVI backup configs...')
    print('********************************\n')

    for loc in [mfwloc,mfwloc.peerloc()]:
        try:
            child = pexpect.spawnu('telnet '+loc.findsw()+'.dn.net')
            child.expect('Username: ')
            child.sendline(username)
            child.expect('Password: ',timeout=3)
            child.sendline(password)
            child.expect('6513-'+loc.findsw()+'-c\d{1,2}#',timeout=3)
            print(loc.findsw()+':\n')
            child.sendline('sh run int vlan '+str(frontVlan))
            child.expect('6513-'+loc.findsw()+'-c\d{1,2}#')
            print(child.before)
            child.sendline('exit')
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Unable to collect switchport configs from '+loc.findsw())
            print('Try collecting configs manually instead:')
            print()
            print('  '+loc.findsw()+':')
            print('    sh run int vlan '+str(frontVlan))
            print()
    input('Hit Enter to view the new SVI configs.')
    print()
    # new SVI configs
    print('************************')
    print('New SVI configs to apply')
    print('************************\n')

    j = 0
    for loc,role in [(mfwloc,'Master'),(mfwloc.peerloc(),'Standby')]:
        sviconfigs = 'telnet '+loc.findsw()+'\n'
        sviconfigs += username+'\n'
        sviconfigs += password+'\n'
        sviconfigs += 'conf t\n'
        sviconfigs += 'no interface vlan '+str(frontVlan)+'\n'
        sviconfigs += 'interface vlan '+str(frontVlan)+'\n'
        sviconfigs += ' desc SHA Solution '+role+' Uplink router - '+alloccode+'-0001\n'
        sviconfigs += ' ip address '+str(frontnets[0][2+j])+' '+str(frontnets[0].netmask)+'\n'
        sviconfigs += ' no ip redirects\n'
        sviconfigs += ' no ip unreachables\n'
        sviconfigs += ' no ip proxy-arp\n'
        sviconfigs += ' ip ospf network non-broadcast\n'
        sviconfigs += ' load-interval 30'
        sviconfigs += ' standby 100 ip '+str(frontnets[0][1])+'\n'
        sviconfigs += ' standby 100 priority '+str(45-j*10)+'\n'
        sviconfigs += ' standby 100 preempt delay minimum 10\n'
        sviconfigs += ' standby 100 authentication ChARTR01\n'
        sviconfigs += ' no shut\n'
        sviconfigs += ' end\n'
        sviconfigs += 'exit\n'
        sviconfigs += '\n'
        j += 1
        print(sviconfigs)


#####THE FOLLOWING FUNCTIONS ARE USED IN HA PROVISIONING SCRIPTS#####

# getHAdevices
# showSummaryHA
# backupPortsHA

def getHAdevices(devicetype):
    """
    devicetype must be either 'firewall' or 'loadbalancer.'
    Prompts to enter SIDs/speed/locations of HA pair & IPS (w/ their error handlings).
    Only accepts the devicetype you specify.
    Returns the provided data as a list for use in main().
    
    mfw = master device ID (firewall or loadbalancer)
    speed = 1000 or 100 (int)
    mfwloc = master device location
    sfw = secondary device ID (firewall or loadbalancer)
    sfwloc = secondary device location
    ips = IPS ID or 'none'
    """
    #import re
    #from networksid import NWdevice
    #from locationcode import Loccode
    while True:
        try:
            mfw = input("Enter the master "+devicetype+" ID: ").lower().strip()
            if NWdevice(mfw).is_master() and NWdevice(mfw).is_fw_or_lb(devicetype):
                mfw = NWdevice(mfw)
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
            mfwloc = Loccode(input("Enter the location code of "+mfw+": "))
            if mfwloc.is_masterloc():
                if mfwloc.site == mfw.site():
                    break
                else:
                    print('ERROR: SITE MISMATCH DETECTED\n')
            else:
                print("ERROR: INVALID LOCATION FOR MASTER\n")
        except AttributeError:
            print("ERROR: INVALID LOCATION\n")
    while True:
        try:
            sfw = mfw.peersid()
            break
        except UnboundLocalError:
            print('\nThis case requires you to provide a secondary '+devicetype+' ID manually.')
            sfw = input('Enter the secondary '+devicetype+' ID: ').lower().strip()
            if re.match(r"^(netsvc)+(\d{5})$", sfw) and NWdevice(sfw) != mfw:
                break
            elif re.match(r"^(netsvc)+(\d{5})$", sfw) and NWdevice(sfw) == mfw:
                print('ERROR: Master and secondary cannot share the same ID!')
    sfwloc = mfwloc.peerloc()
    print('OK')
    print("The location of secondary "+sfw+" is {0}.".format(sfwloc))
    while True:
        try:
            ips = input("Enter an IPS ID that goes to the master segment, or type 'none': ").lower().strip().replace("'","")

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
                if ipsloc.is_NWloc() and (mfwloc.srr == ipsloc.srr and mfwloc.rack_noa == ipsloc.rack_noa) and mfwloc != ipsloc:
                    print("OK")
                    break
                elif mfwloc == ipsloc:
                    print("ERROR: Master "+devicetype+" and IPS cannot take the same slot!\n")
                elif not (mfwloc.srr == ipsloc.srr and mfwloc.rack_noa == ipsloc.rack_noa):
                    print("ERROR: Master "+devicetype+" and IPS must be in the same rack\n")
                else:
                    print("ERROR: INVALID LOCATION\n")
            except AttributeError:
                print("ERROR: SYNTAX INVALID\n")
    else:
        ipsloc = ''
        print("OK no IPS!")
    return [mfw,speed,mfwloc,sfw,sfwloc,ips,ipsloc]

def showSummaryHA(master,masterloc,secondary,secondaryloc,IPS,IPSloc):
    #from locationcode import Loccode
    #from networksid import NWdevice
    if IPS != 'none':
        Devices = [[master,masterloc],
                   [secondary,secondaryloc],
                   [IPS,IPSloc]]
    else:
        Devices = [[master,masterloc],
                   [secondary,secondaryloc]]
    output = '\n'
    output += 'The standard front/back switchports of the devices that you entered:\n\n'
    for sid,loc in Devices:
        output += sid+' ('+loc+'):\n'
        output += ' Front: '+loc.findsw()+' '+loc.findfrport()+'\n'
        output += ' Back:  '+loc.findsw()+' '+loc.findbkport()+'\n\n'
    print(output)

def backupPortsHA(mfwloc,ipsloc,username,password,Ports,ips):
    # back up port configs
    #import pexpect
    #from pexpect import EOF
    #from pexpect import TIMEOUT
    #from pexpect import ExceptionPexpect
    #from locationcode import Loccode
    #from networksid import NWdevice
    print('***************************************')
    print('Collecting switchport backup configs...')
    print('***************************************\n')
    
    backups = [(mfwloc,'5'),(mfwloc.peerloc(),'6')]
    for loc,mod in backups:
        try:
            child = pexpect.spawnu('telnet '+loc.findsw()+'.dn.net')
            child.expect('Username: ')
            child.sendline(username)
            child.expect('Password: ',timeout=3)
            child.sendline(password)
            child.expect('6513-'+loc.findsw()+'-c\d{1,2}#',timeout=3)
            print(loc.findsw()+':\n')
            child.sendline('sh run int '+loc.findfrport())
            child.expect('6513-'+loc.findsw()+'-c\d{1,2}#')
            print(child.before)
            child.sendline('sh run int '+loc.findbkport())
            child.expect('6513-'+loc.findsw()+'-c\d{1,2}#')
            print(child.before)
            for port in Ports[2:]:
                child.sendline('sh run int gi'+loc.findmod()+'/'+str(port))
                child.expect('6513-'+loc.findsw()+'-c\d{1,2}#')
                print(child.before)
            if ips != 'none' and loc.findsw() == ipsloc.findsw():
                child.sendline('sh run int '+ipsloc.findfrport())
                child.expect('6513-'+ipsloc.findsw()+'-c\d{1,2}#')
                print(child.before)
                child.sendline('sh run int '+ipsloc.findbkport())
                child.expect('6513-'+ipsloc.findsw()+'-c\d{1,2}#')
                print(child.before)
            child.sendline('exit')
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Unable to collect switchport configs from '+loc.findsw())
            print('Try collecting configs manually instead:')
            print()
            print('  '+loc.findsw()+':')
            print('    sh run int '+loc.findfrport())
            print('    sh run int '+loc.findbkport())
            for port in Ports[2:]:
                print('    sh run int gi'+loc.findmod()+'/'+str(port))
            if ips != 'none' and ipsloc.findmod() == mod:
                print('    sh run int '+ipsloc.findfrport())
                print('    sh run int '+ipsloc.findbkport())
            print()

#####THE FOLLOWING FUNCTIONS ARE USED IN NON-HA PROVISIONING SCRIPTS#####

# getDevices
# showSummary
# backupPorts

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
            nwdevice = NWdevice(input("Enter the "+devicetype+" ID: ").lower().strip())
            if nwdevice.is_fw_or_lb(devicetype) and nwdevice.is_solo():
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
                if nwdeviceloc.site == nwdevice.site():
                    break
                else:
                    print('ERROR: SITE MISMATCH DETECTED\n')
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

def showSummary(nwdevice,nwdeviceloc,IPS,IPSloc):
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

def backupPorts(mfwloc,ipsloc,username,password,Ports,ips):
    # back up port configs
    #import pexpect
    #from pexpect import EOF
    #from pexpect import TIMEOUT
    #from pexpect import ExceptionPexpect
    print('***************************************')
    print('Collecting switchport backup configs...')
    print('***************************************\n')
    
    try:
        child = pexpect.spawnu('telnet '+mfwloc.findsw()+'.dn.net')
        child.expect('Username: ')
        child.sendline(username)
        child.expect('Password: ',timeout=3)
        child.sendline(password)
        child.expect('6513-'+mfwloc.findsw()+'-c\d{1,2}#',timeout=3)
        print(mfwloc.findsw()+':\n')
        child.sendline('sh run int '+mfwloc.findfrport())
        child.expect('6513-'+mfwloc.findsw()+'-c\d{1,2}#')
        print(child.before)
        child.sendline('sh run int '+mfwloc.findbkport())
        child.expect('6513-'+mfwloc.findsw()+'-c\d{1,2}#')
        print(child.before)
        for port in Ports[2:]:
            child.sendline('sh run int gi'+mfwloc.findmod()+'/'+str(port))
            child.expect('6513-'+mfwloc.findsw()+'-c\d{1,2}#')
            print(child.before)
        child.sendline('exit')
    except (EOF,TIMEOUT,ExceptionPexpect):
        print('ERROR: Unable to collect switchport backups from '+mfwloc.findsw())
        print('Try collecting configs manually instead:\n')
        print('  '+mfwloc.findsw()+':')
        print('    sh run int '+mfwloc.findfrport())
        print('    sh run int '+mfwloc.findbkport())
        for port in Ports[2:]:
            print('    sh run int gi'+mfwloc.findmod()+'/'+str(port))
        print()

    if ips != 'none':
        try:
            child2 = pexpect.spawnu('telnet '+ipsloc.findsw()+'.dn.net')
            child2.expect('Username: ')
            child2.sendline(username)
            child2.expect('Password: ',timeout=3)
            child2.sendline(password)
            child2.expect('6513-'+ipsloc.findsw()+'-c\d{1,2}#',timeout=3)
            if mfwloc.findmod() != ipsloc.findmod():
                print('\n'+ipsloc.findsw()+':\n')
            child2.sendline('sh run int '+ipsloc.findfrport())
            child2.expect('6513-'+ipsloc.findsw()+'-c\d{1,2}#')
            print(child2.before)
            child2.sendline('sh run int '+ipsloc.findbkport())
            child2.expect('6513-'+ipsloc.findsw()+'-c\d{1,2}#')
            print(child2.before)
            child2.sendline('exit')
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Unable to collect IPS switchport backups from '+ipsloc.findsw())
            print('Try collecting configs manually instead:\n')
            print('  '+ipsloc.findsw()+':')
            print('    sh run int '+ipsloc.findfrport())
            print('    sh run int '+ipsloc.findbkport())
            print()

#####THE FOLLOWING FUNCTIONS ARE USED IN IPS-ONLY PROVISIONING SCRIPT#####

# getIPS
# getIPSmgtInfo
# getNWdevice
# getItf_and_port
# showIPSCabling

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
                if ipsloc.site == ips.site():
                    break
                else:
                    print('ERROR: SITE MISMATCH DETECTED\n')
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

def getNWdevice(number,ipsloc):
    """
    Prompts to enter SIDs/speed/locations of a network device.
    nwdevice = newtwork device ID (firewall or loadbalancer)
    speed = 1000 or 100 (int)
    nwdeviceloc = network device location
    number: monitored device number (1 or 2) - used only in prompt messages
    """

    def __sidlocMISmatch(nwdevice,deviceloc):
        """
        Helper Boolean that warns an invalid SID-LOCATION combination.
        Returns True if MISmatch is found.
        """
        return (nwdevice.is_master() and not deviceloc.is_masterloc()) or (nwdevice.is_secondary() and deviceloc.is_masterloc())

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

def showIPSCabling(ips,nwdevice,nwdeviceloc,segmentName,deviceitf,pnum,monnum):
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

    cabling = segmentName+':\n'
    cabling += '  '+nwdevice+' '+deviceitf+' -> GREEN XOVER -> '+ips+' port '+to_nwdevice+'\n'
    cabling += '  '+ips+' port '+to_switch+' -> GREEN STRAIGHT -> U'+bk+' '+updown+' ORANGE PANEL p'+pnum+'\n'
    print(cabling)


