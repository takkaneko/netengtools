#!/usr/bin/env python3
# flexresources.py

import re
import getpass
import pexpect
from pexpect import EOF
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect
from locationcode import Loccode

########################################################
# FUNCTIONS THAT ARE COMMONLY USED FOR BOTH IAD AND SJC:
########################################################

def getUPA2():
    # Appended '2' to the function name to differentiate this from the existing getUPA function
    # in resources.py file. The only difference is that alloc is actually alloccode-depth.
    
    username = ''
    while username == '':
        username = input('Enter your tacacs username: ').strip().lower()
    password = ''
    while password == '':
        password = getpass.getpass(prompt='Enter your tacacs password: ',stream=None).strip()
    while True:
        try:
            alloc = input('Enter an allocation/depth codes (e.g, "nttages-9902"): ').strip().lower()
            if not re.match(r"\w+-\d{4}",alloc):
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return [username,password,alloc]

def getVLAN2():
    # Appended '2' to the function name to differentiate this from the existing getVLAN function
    # in resources.py file.
    while True:
        try:
            vlan = int(input('Enter a VLAN ID: '))
            if vlan <= 0 or 4096 < vlan:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return vlan
    
    
def getSID():
    while True:
        try:
            sid = input('Enter a server ID: ').strip().lower()
            if not re.match(r"^[a-z]+\d{5}$",sid):
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return sid

def os_and_speed(sid):
    # Does the following things:
    #
    #  1. Determines the OS type (windows/linux/sun/other)
    #  2. Determines auto/auto or 1000/full or 100/full
    #  3. Returns the following values:
    #     (1) os...OS type
    #     (2) negotiate...'y' or 'n'
    #     (3) speed...'auto' or '1000' or '100'. To be used in configs.
    #     (4) duplex...'duplex full' or 'no duplex'. To be used in configs.
    #     (5) spd...'1000' or '100'. To be used in cabling instructions.
    
    if sid[0] == 'w' or sid[0:3] == 'itw' or sid[0:3] == 'isw':
        os = 'windows'
        negotiate = 'n'
    elif sid[0] == 'l' or sid[0:3] == 'itl' or sid[0:3] == 'isl':
        os = 'linux'
        negotiate = 'y'
    elif sid[0:3] == 'sun':
        os = 'sun'
        negotiate = 'n'
    else:
        os = 'other'
    if os == 'other':
        while True:
            try:
                negotiate = input('Auto negotiate [y/n]?: ').strip().lower()[0]
                if not negotiate == 'y' and not negotiate == 'n':
                    print('ERROR: DATA INVALID')
                else:
                    break
            except (ValueError,IndexError):
                print('ERROR: DATA INVALID')
    if negotiate == 'n':
        while True:
            try:
                speed = input('Speed (1000/100)[1000]?: ').strip() or '1000'
                if not re.match(r"^10{2,3}$",speed):
                    print('ERROR: DATA INVALID')
                else:
                    break
            except ValueError:
                print('ERROR: DATA INVALID')
        duplex = 'duplex full'
    else:
        speed = 'auto'
        duplex = 'no duplex'
    spd = '100' if speed == '100' else '1000'
    return [os,negotiate,speed,duplex,spd]

def identify_switches(loc):
    # Returns the four switches (p1/p2/s1/s2) the location has connections to
    loc = Loccode(loc)
    if loc.sr == 'sjc.c10':
        sw = 'sjc1'
    elif loc.sr == 'sjc.c4':
        sw = 'sjc4'
    elif loc.sr == 'sjc.c9':
        sw = 'sjc9'
    elif loc.sr == 'iad.c4':
        sw = 'iad4'
    swprfx = sw+loc.row.zfill(2)
    SWp1 = swprfx+'p1'
    SWp2 = swprfx+'p2'
    SWs1 = swprfx+'s1'
    SWs2 = swprfx+'s2'
    return [SWp1,SWp2,SWs1,SWs2]

def identify_switch_roles(trace,SWp1,SWp2,SWs1,SWs2):
    # Primary roles between p1 and p2, and betweeen s1 and s2
    # depend on whether the rack is straight or reversed
    priSW = SWp1 if trace == 'straight' else SWp2
    pr2SW = SWp2 if trace == 'straight' else SWp1
    secSW = SWs1 if trace == 'straight' else SWs2
    se2SW = SWs2 if trace == 'straight' else SWs1
    return [priSW,pr2SW,secSW,se2SW]

def get_cabling_type():
    # available cabling types are:
    # 
    #     HA: hbeat,vmotion,pri+,sec+,otherha
    # Non-HA: ilo,other
    print('Now please specify the cabling type. Available types are:')
    print()
    print('    hbeat: Heartbeat (HA)')
    print('  vmotion: Vmotion (HA)')
    print('     pri+: Add\'tl primarynet (HA)')
    print('     sec+: Add\'tl secnet (HA)')
    print('      ilo: Routable ilo (Non-HA)')
    print('  otherha: Other (HA)')
    print('    other: Other (Non-HA)')
    while True:
        try:
            type = input('Cable type of your choice: ').strip().lower()
            if not type in ['hbeat','vmotion','pri+','sec+','ilo','otherha','other']:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    return type

def identify_cabling_attributes(type):
    # dual...determines if the cabling is HA or not. 
    # custom_type...need to name the otherha/other cabling.
    # pri_or_sec...automatically set when obvious. manually 
    #              claim one when the type is otherha/other.
    if type in ['hbeat','vmotion','pri+','sec+','otherha']:
        dual = 'y'
    else:
        dual = 'n'

    if type in ['otherha','other']:
        custom_type = ''
        while custom_type == '':
            custom_type = input('Name this cabling type (eg, "DMZ2", "sec3". etc.): ').strip().title()
        while True:
            try:
                pri_or_sec = input('Should this use primarynet or secnet? [pri/sec]: ').strip().lower()
                if not pri_or_sec in ['pri','sec']:
                    print('ERROR: DATA INVALID\n')
                else:
                    break
            except (ValueError,IndexError):
                print('ERROR: DATA INVALID\n')
    elif type in ['hbeat','vmotion','pri+','ilo']:
        custom_type = 'n/a'
        pri_or_sec = 'pri'
    else: # if type == 'sec+'
        custom_type = 'n/a'
        pri_or_sec = 'sec'
    return [dual,custom_type,pri_or_sec]

def typeDictionary(custom_type):
    # a dictionary of cabling types (keys) for their associated strings (values)
    # that will be used in configs and cabling instructions
    typeDict = {'hbeat': ('Heartbeat','hbt','hb2'),
          'vmotion': ('Vmotion','vmo','vm2'),
          'pri+': ('Add\'tl primarynet', 'pri','pr2'),
          'sec+': ('Add\'tl secnet','sec','se2'),
          'ilo': ('Routable ilo','ilo','ilo'),
          'otherha': (custom_type,'other','othr2'),
          'other': (custom_type,'other','other')}
    return typeDict

def summaryView(alloc,sid,os,negotiate,loc,trace,priSW,
                pr2SW,secSW,se2SW,vlan,type,dual,custom_type,pri_or_sec):
    print()
    print('You entered:')
    print()
    print('  Allocation-depth: '+alloc)
    print('         Server ID: '+sid)
    print('           OS type: '+os+' (Auto negotiate = '+negotiate+')')
    print('     Location code: '+loc)
    print('     This is a '+trace+' rack.')
    print('      Prim1 Switch: '+priSW)
    print('      Prim2 Switch: '+pr2SW)
    print('       Sec1 Switch: '+secSW)
    print('       Sec2 Switch: '+se2SW)
    print('              VLAN: '+str(vlan))
    print('      Cabling Type: '+type+' (Dual cabling = '+dual+')')
    if type ==  'otherha' or 'other':
        print('Custom cabling name: '+custom_type)
        print('       Used network: '+pri_or_sec)

def switch_pair(type,pri_or_sec,SWp1,SWp2,SWs1,SWs2):
    # sw_pair is always either p1-p2 or s1-s2
    # SW1 is always p1 or s1
    # SW2 is always p2 or s2
    if type == 'hbeat' or type == 'vmotion' or type == 'pri+' or type == 'ilo':
        sw_pair = SWp1+'-'+SWp2
        SW1 = SWp1
        SW2 = SWp2
    elif (type == 'otherha' or type == 'other') and pri_or_sec == 'pri':
        sw_pair = SWp1+'-'+SWp2
        SW1 = SWp1
        SW2 = SWp2
    elif (type == 'otherha' or type == 'other') and pri_or_sec == 'sec':
        sw_pair = SWs1+'-'+SWs2
        SW1 = SWs1
        SW2 = SWs2
    else: # type == 'sec+'
        sw_pair = SWs1+'-'+SWs2
        SW1 = SWs1
        SW2 = SWs2
    return [sw_pair,SW1,SW2]

def check_swport_usage(sw_pair,SW1,SW2,username,password):
    # uses pexpect to obtain switchport status outputs from SW1 and SW2
    print()
    input('Hit Enter to check the switchport statuses on '+sw_pair+':')
    print()
    for switch in [SW1,SW2]:
        try:
            child = pexpect.spawnu('telnet '+switch+'.dn.net')
            child.expect('Username: ',timeout=3)
            child.sendline(username)
            child.expect('Password: ',timeout=3)
            child.sendline(password)
            child.expect('6513-'+switch+'-(sec-)*c\d{1,2}#',timeout=3)
            print('====================================')
            print(switch+':\n')
            child.sendline('term len 55')
            child.expect('6513-'+switch+'-(sec-)*c\d{1,2}#',timeout=3)
            child.sendline('sh int status mod 4')
            child.expect('Gi4/25',timeout=3)
            print(child.before)
            child.sendline('exit')
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Unable to display mod 4 interface statuses from '+switch)
            print('Try checking statuses manually instead:')
            print()
            print('  '+switch+':')
            print('    sh int status mod 4')
            print()

        try:
            child = pexpect.spawnu('telnet '+switch+'.dn.net')
            child.expect('Username: ')
            child.sendline(username)
            child.expect('Password: ',timeout=3)
            child.sendline(password)
            child.expect('6513-'+switch+'-(sec-)*c\d{1,2}#',timeout=3)
            child.sendline('term len 55')
            child.expect('6513-'+switch+'-(sec-)*c\d{1,2}#',timeout=3)
            child.sendline('sh int status mod 4 | beg Gi4/25')
            child.expect('6513-'+switch+'-(sec-)*c\d{1,2}#',timeout=3)
            print(child.before)
            child.sendline('exit')
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Unable to display mod 4 interface statuses from '+switch)
            print('Try checking statuses manually instead:')
            print()
            print('  '+switch+':')
            print('    sh int status mod 4')
            print()

def choose_sw1_or_sw2(SW1,SW2):
    # Single cabling cases require a user to choose either SW1 or SW2
    while True:
        try:
            use_this_switch = input('Choose '+SW1+' or '+SW2+' to use this time: ').strip().lower()
            if not use_this_switch in [SW1,SW2]:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    return use_this_switch

def choose_switchport(use_this_switch):
    # non-HA
    while True:
        try:
            port = input('Choose '+use_this_switch+' module 4 SWITCHPORT number to use this time (1 - 48): ').strip()
            if not 1<=int(port)<=48:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    return port

def ask_symmetric_or_not():
    while True:
        try:
            symmetric = input('Symmetric cabling (switchports)? [Y/n]: ').strip().lower()[0]
            if not symmetric in ['y','n']:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    return symmetric

def choose_switchports_HA(SW1,SW2,symmetric):
    while True:
        try:
            port1 = input('Choose the '+SW1+' module 4 SWITCHPORT number to use this time (1 - 48): ').strip()
            if not int(port1) in [i for i in range(1,49)]:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    if symmetric == 'n':
        while True:
            try:
                port2 = input('Choose the '+SW2+' port number: ').strip()
                if not int(port2) in [i for i in range(1,49)]:
                    print('ERROR: DATA INVALID\n')
                else:
                    break
            except (ValueError,IndexError):
                print('ERROR: DATA INVALID\n')
    else:
        port2 = port1
    return [port1,port2]

def ask_more(vlan,type):
    while True:
        try:
            more = input('Need to provision more server(s) for the same segment/type '
                         '(VLAN'+str(vlan)+'/'+type+')?[y/N]: ').strip().lower()[0]
            if not more in ['y','n']:
                print('ERROR: DATA INVALID; TRY AGAIN\n')
            else:
                break
        except IndexError:
            print('ERROR: DATA INVALID; TRY AGAIN\n')
    return more

###########################################
# FUNCTIONS THAT ARE INTENDED ONLY FOR SJC:
###########################################

def getLOC_SJC():
    # Prompts for a location and returns it as a Loccode object that is valid for SJC Boreas.
    while True:
        try:
            loc = input('Enter a location code: ').strip().lower()
            loc = Loccode(loc)
            if not int(loc.rack) in [4,5,6,8,9,10,11,12,13,14,15,16,17,18,20,21]:
                print("ERROR: INVALID LOCATION\n")
            elif not 1<=int(loc.slot)<=12:
                print("ERROR: INVALID LOCATION\n")
            elif not loc.sr in ['sjc.c10','sjc.c4','sjc.c9']:
                print("ERROR: INVALID LOCATION\n")
            elif not int(loc.row) in [1,2,3,4]:
                print("ERROR: INVALID LOCATION\n")
            else:
                break
        except AttributeError:
            print("ERROR: INVALID LOCATION\n")
    return loc

def idf_U_number_SJC(loc):
    # Returns the U number (as a string) of the patch panel in the IDF racks.
    if int(loc.rack) in [4,5,6,8]:
        u_num = '5'
    elif int(loc.rack) in [9,10,11,12]:
        u_num = '4'
    elif int(loc.rack) in [13,14,15,16]:
        u_num = '3'
    else: # int(loc.rack) in [17,18,20,21]
        u_num = '2'
    return u_num

def determine_trace_SJC(loc):
    # straight or reversed
    sjc_straight_racks = [4,6,9,11,13,15,17,20]
    sjc_reverse_racks = [5,8,10,12,14,16,18,21]
    if int(loc.rack) in sjc_straight_racks:
        trace = 'straight'
    else:
        trace = 'reversed'
    return trace

def choose_flexport_SJC(use_this_switch,SW1,loc):
    # non-HA
    flexpt_range = '1 - 12' if use_this_switch == SW1 else '25 - 36'
    flexpt_range_real = [i for i in range(1,13)] if use_this_switch == SW1 else [i for i in range(25,37)]
    idf_num = '2' if use_this_switch == SW1 else '23'
    while True:
        try:
            flexport = input('Select an available FLEX port in the server rack ('+flexpt_range+'): ').strip()
            if not int(flexport) in flexpt_range_real:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    flxpt_base = int(flexport)%24
    if loc.rack in ['4','9','13','17']:
        idf_port = str(flxpt_base)
    elif loc.rack in ['5','10','14','18']:
        idf_port = str(flxpt_base + 12)
    elif loc.rack in ['6','11','15','20']:
        idf_port = str(flxpt_base + 24)
    else: # if loc.rack in ['8','12','16','21']:
        idf_port = str(flxpt_base + 36)
    return [flexport,idf_port,idf_num]

def print_results_SJC(sid,loc,spd,type,typeDict,flexport,idf_num,u_num,idf_port,
                      use_this_switch,port,alloc,vlan,pri_or_sec,speed,duplex):
    # non-HA
    print()
    print('*******************')
    print('CABLING INSTUCTIONS')
    print('*******************')
    print()
    print(sid+' ('+loc+')')
    print()
    print(typeDict[type][0]+':')
    print()
    print('Speed/Dup: '+spd+'/Full')
    print()
    print(' '+typeDict[type][0]+' interface ->')
    print('  PURPLE STRAIGHT -> U43 purple panel port '+flexport+' ->')
    print('  PURPLE STRAIGHT -> rack '+loc.row+'-'+idf_num)
    print('  PURPLE STRAIGHT -> purple panel U'+u_num+' p'+idf_port+' ->')
    print('  PURPLE STRAIGHT -> '+use_this_switch+' gi4/'+port)
    print()
    print('*************************')
    print('SWITCHPORT CONFIGURATIONS')
    print('*************************')
    print()
    print(use_this_switch+':')
    print()
    print('interface GigabitEthernet4/'+port)
    print(' description '+loc.row+'-'+loc.rack+'-'+loc.slot+'-'+typeDict[type][1]+' '+alloc+' server - '+sid)
    print(' switchport')
    print(' switchport access vlan '+str(vlan))
    if pri_or_sec == 'pri':
        print(' switchport mode access')
    else:
        print(' private-vlan host-association 11 '+str(vlan))
        print(' switchport mode private-vlan host')
    print(' load-interval 30')
    print(' speed '+speed)
    print(' '+duplex)
    print(' spanning-tree portfast edge')
    print(' no shut')
    print('end')
    print()

def choose_flexports_SJC_HA(trace,loc,pri_or_sec,priSW,pr2SW,secSW,se2SW,port1,port2):
    while True:
        try:
            flexport1 = input('Select an available U43 FLX1 port (1 - 12) in the server rack: ').strip()
            if not int(flexport1) in [i for i in range(1,13)]:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    while True:
        try:
            ask_symmetric_flex = input('Use the symmetric FLX2 port '+str(int(flexport1)+24)+'? [Y/n]: ').strip().lower()
            if not ask_symmetric_flex in ['y','n']:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    if ask_symmetric_flex == 'y':
        flexport2 = str(int(flexport1)+24)
    else:
        while True:
            try:
                flexport2 = input('Select an available U43 FLX2 port (25 - 36) in the server rack: ').strip()
                if not int(flexport2) in [i for i in range(25,37)]:
                    print('ERROR: DATA INVALID\n')
                else:
                    break
            except (ValueError,IndexError):
                print('ERROR: DATA INVALID\n')
    prim_flexport = flexport1 if trace == 'straight' else flexport2
    sec_flexport = flexport2 if trace == 'straight' else flexport1
    prim_idf_num = '2' if trace == 'straight' else '23'
    sec_idf_num = '23' if trace == 'straight' else '2'
    if loc.rack in ['4','9','13','17']:
        idf_port = flexport1
    elif loc.rack in ['5','10','14','18']:
        idf_port = str(int(flexport1) + 12)
    elif loc.rack in ['6','11','15','20']:
        idf_port = str(int(flexport1) + 24)
    else: # if loc.rack in ['8','12','16','21']:
        idf_port = str(int(flexport1) + 36)
    prim_sw = priSW if pri_or_sec == 'pri' else secSW
    sec_sw = pr2SW if pri_or_sec == 'pri' else se2SW
    prim_port = port1 if trace == 'straight' else port2
    sec_port = port2 if trace == 'straight' else port1
    return [prim_flexport,sec_flexport,idf_port,prim_idf_num,sec_idf_num,prim_sw,sec_sw,prim_port,sec_port]

def print_results_SJC_HA(sid,loc,typeDict,type,spd,
                         prim_flexport,prim_idf_num,u_num,
                         idf_port,prim_sw,prim_port,
                         sec_flexport,sec_idf_num,sec_sw,sec_port,
                         alloc,vlan,pri_or_sec,speed,duplex):
    print()
    print('*******************')
    print('CABLING INSTUCTIONS')
    print('*******************')
    print()
    print(sid+' ('+loc+')')
    print()
    print(typeDict[type][0]+':')
    print()
    print('Speed/Dup: '+spd+'/Full')
    print()
    print(' '+typeDict[type][0]+' prim.interface ->')
    print('  PURPLE STRAIGHT -> U43 purple panel port '+prim_flexport+' ->')
    print('  PURPLE STRAIGHT -> rack '+loc.row+'-'+prim_idf_num)
    print('  PURPLE STRAIGHT -> purple panel U'+u_num+' p'+idf_port+' ->')
    print('  PURPLE STRAIGHT -> '+prim_sw+' gi4/'+prim_port)
    print()
    print(' '+typeDict[type][0]+' sec.interface ->')
    print('  PURPLE STRAIGHT -> U43 purple panel port '+sec_flexport+' ->')
    print('  PURPLE STRAIGHT -> rack '+loc.row+'-'+sec_idf_num)
    print('  PURPLE STRAIGHT -> purple panel U'+u_num+' p'+idf_port+' ->')
    print('  PURPLE STRAIGHT -> '+sec_sw+' gi4/'+sec_port)
    print()
    print('*************************')
    print('SWITCHPORT CONFIGURATIONS')
    print('*************************')
    print()
    print(prim_sw+':')
    print()
    print('interface GigabitEthernet4/'+prim_port)
    print(' description '+loc.row+'-'+loc.rack+'-'+loc.slot+'-'+typeDict[type][1]+' '+alloc+' server - '+sid)
    print(' switchport')
    print(' switchport access vlan '+str(vlan))
    if pri_or_sec == 'pri':
        print(' switchport mode access')
    else:
        print(' private-vlan host-association 11 '+str(vlan))
        print(' switchport mode private-vlan host')
    print(' load-interval 30')
    print(' speed '+speed)
    print(' '+duplex)
    print(' spanning-tree portfast edge')
    print(' no shut')
    print('end')
    print()
    print(sec_sw+':')
    print()
    print('interface GigabitEthernet4/'+sec_port)
    print(' description '+loc.row+'-'+loc.rack+'-'+loc.slot+'-'+typeDict[type][2]+' '+alloc+' server - '+sid)
    print(' switchport')
    print(' switchport access vlan '+str(vlan))
    if pri_or_sec == 'pri':
        print(' switchport mode access')
    else:
        print(' private-vlan host-association 11 '+str(vlan))
        print(' switchport mode private-vlan host')
    print(' load-interval 30')
    print(' speed '+speed)
    print(' '+duplex)
    print(' spanning-tree portfast edge')
    print(' no shut')
    print('end')
    print()

###########################################
# FUNCTIONS THAT ARE INTENDED ONLY FOR IAD:
###########################################

def getLOC_IAD():
    # Prompts for a location and returns it as a Loccode object that is valid for IAD Boreas.
    while True:
        try:
            loc = input('Enter a location code: ').strip().lower()
            loc = Loccode(loc)
            if not int(loc.rack) in range(4,12):
                print("ERROR: INVALID LOCATION\n")
            elif not 1<=int(loc.slot)<=24:
                print("ERROR: INVALID LOCATION\n")
            elif not loc.sr in ['iad.c4']:
                print("ERROR: INVALID LOCATION\n")
            elif not int(loc.row) in [1,2,3,4,11]:
                print("ERROR: INVALID LOCATION\n")
            else:
                break
        except AttributeError:
            print("ERROR: INVALID LOCATION\n")
    return loc

def idf_U_number_IAD(loc):
    # Returns the U number (as a string) of the patch panel in the IDF racks.
    if int(loc.rack) in [4,5,6,7]:
        u_num = '6'
    else: # int(loc.rack) in [8,9,10,11]
        u_num = '5'
    return u_num

def determine_trace_IAD(loc):
    # straight or reversed
    iad_straight_racks = [4,6,8,10]
    iad_reverse_racks = [5,7,9,11]
    if int(loc.rack) in iad_straight_racks:
        trace = 'straight'
    else:
        trace = 'reversed'
    return trace

def choose_flexport_IAD(use_this_switch,SW1,loc):
    # non-HA
    flexpt_range = '25 - 36' if use_this_switch == SW1 else '37 - 48'
    flexpt_range_real = [i for i in range(25,37)] if use_this_switch == SW1 else [i for i in range(37,49)]
    idf_num = '2' if use_this_switch == SW1 else '13'
    while True:
        try:
            flexport = input('Select an available FLEX port in the server rack ('+flexpt_range+'): ').strip()
            if not int(flexport) in flexpt_range_real:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    flxpt_base = int(flexport)%24 if int(flexport) in range(25,37) else int(flexport)%36
    if loc.rack in ['4','8']:
        idf_port = str(flxpt_base)
    elif loc.rack in ['5','9']:
        idf_port = str(flxpt_base + 12)
    elif loc.rack in ['6','10']:
        idf_port = str(flxpt_base + 24)
    else: # if loc.rack in ['7','11']:
        idf_port = str(flxpt_base + 36)
    return [flexport,idf_port,idf_num]

def print_results_IAD(sid,loc,spd,type,typeDict,flexport,idf_num,u_num,idf_port,
                      use_this_switch,port,alloc,vlan,pri_or_sec,speed,duplex):
    # non-HA
    print()
    print('*******************')
    print('CABLING INSTUCTIONS')
    print('*******************')
    print()
    print(sid+' ('+loc+')')
    print()
    print(typeDict[type][0]+':')
    print()
    print('Speed/Dup: '+spd+'/Full')
    print()
    print(' '+typeDict[type][0]+' interface ->')
    print('  PURPLE STRAIGHT -> U51 purple panel port '+flexport+' ->')
    print('  PURPLE STRAIGHT -> rack '+loc.row+'-'+idf_num)
    print('  PURPLE STRAIGHT -> purple panel U'+u_num+' p'+idf_port+' ->')
    print('  PURPLE STRAIGHT -> '+use_this_switch+' gi4/'+port)
    print()
    print('*************************')
    print('SWITCHPORT CONFIGURATIONS')
    print('*************************')
    print()
    print(use_this_switch+':')
    print()
    print('interface GigabitEthernet4/'+port)
    print(' description '+loc.row+'-'+loc.rack+'-'+loc.slot+'-'+typeDict[type][1]+' '+alloc+' server - '+sid)
    print(' switchport')
    print(' switchport access vlan '+str(vlan))
    if pri_or_sec == 'pri':
        print(' switchport mode access')
    else:
        print(' private-vlan host-association 11 '+str(vlan))
        print(' switchport mode private-vlan host')
    print(' load-interval 30')
    print(' speed '+speed)
    print(' '+duplex)
    print(' spanning-tree portfast edge')
    print(' no shut')
    print('end')
    print()

def choose_flexports_IAD_HA(trace,loc,pri_or_sec,priSW,pr2SW,secSW,se2SW,port1,port2):
    while True:
        try:
            flexport1 = input('Select an available U51 FLX1 port (25 - 36) in the server rack: ').strip()
            if not int(flexport1) in [i for i in range(25,37)]:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    while True:
        try:
            ask_symmetric_flex = input('Use the symmetric FLX2 port '+str(int(flexport1)+12)+'? [Y/n]: ').strip().lower()
            if not ask_symmetric_flex in ['y','n']:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except (ValueError,IndexError):
            print('ERROR: DATA INVALID\n')
    if ask_symmetric_flex == 'y':
        flexport2 = str(int(flexport1)+12)
    else:
        while True:
            try:
                flexport2 = input('Select an available U51 FLX2 port (37 - 48) in the server rack: ').strip()
                if not int(flexport2) in [i for i in range(37,49)]:
                    print('ERROR: DATA INVALID\n')
                else:
                    break
            except (ValueError,IndexError):
                print('ERROR: DATA INVALID\n')
    prim_flexport = flexport1 if trace == 'straight' else flexport2
    sec_flexport = flexport2 if trace == 'straight' else flexport1
    prim_idf_num = '2' if trace == 'straight' else '13'
    sec_idf_num = '13' if trace == 'straight' else '2'
    flxpt_base = str(int(flexport1)%24)
    if loc.rack in ['4','8']:
        idf_port = flxpt_base
    elif loc.rack in ['5','9']:
        idf_port = str(int(flxpt_base) + 12)
    elif loc.rack in ['6','10']:
        idf_port = str(int(flxpt_base) + 24)
    else: # if loc.rack in ['7','11']:
        idf_port = str(int(flxpt_base) + 36)
    prim_sw = priSW if pri_or_sec == 'pri' else secSW
    sec_sw = pr2SW if pri_or_sec == 'pri' else se2SW
    prim_port = port1 if trace == 'straight' else port2
    sec_port = port2 if trace == 'straight' else port1
    return [prim_flexport,sec_flexport,idf_port,prim_idf_num,sec_idf_num,prim_sw,sec_sw,prim_port,sec_port]

def print_results_IAD_HA(sid,loc,typeDict,type,spd,
                         prim_flexport,prim_idf_num,u_num,
                         idf_port,prim_sw,prim_port,
                         sec_flexport,sec_idf_num,sec_sw,sec_port,
                         alloc,vlan,pri_or_sec,speed,duplex):
    print()
    print('*******************')
    print('CABLING INSTUCTIONS')
    print('*******************')
    print()
    print(sid+' ('+loc+')')
    print()
    print(typeDict[type][0]+':')
    print()
    print('Speed/Dup: '+spd+'/Full')
    print()
    print(' '+typeDict[type][0]+' prim.interface ->')
    print('  PURPLE STRAIGHT -> U51 purple panel port '+prim_flexport+' ->')
    print('  PURPLE STRAIGHT -> rack '+loc.row+'-'+prim_idf_num)
    print('  PURPLE STRAIGHT -> purple panel U'+u_num+' p'+idf_port+' ->')
    print('  PURPLE STRAIGHT -> '+prim_sw+' gi4/'+prim_port)
    print()
    print(' '+typeDict[type][0]+' sec.interface ->')
    print('  PURPLE STRAIGHT -> U51 purple panel port '+sec_flexport+' ->')
    print('  PURPLE STRAIGHT -> rack '+loc.row+'-'+sec_idf_num)
    print('  PURPLE STRAIGHT -> purple panel U'+u_num+' p'+idf_port+' ->')
    print('  PURPLE STRAIGHT -> '+sec_sw+' gi4/'+sec_port)
    print()
    print('*************************')
    print('SWITCHPORT CONFIGURATIONS')
    print('*************************')
    print()
    print(prim_sw+':')
    print()
    print('interface GigabitEthernet4/'+prim_port)
    print(' description '+loc.row+'-'+loc.rack+'-'+loc.slot+'-'+typeDict[type][1]+' '+alloc+' server - '+sid)
    print(' switchport')
    print(' switchport access vlan '+str(vlan))
    if pri_or_sec == 'pri':
        print(' switchport mode access')
    else:
        print(' private-vlan host-association 11 '+str(vlan))
        print(' switchport mode private-vlan host')
    print(' load-interval 30')
    print(' speed '+speed)
    print(' '+duplex)
    print(' spanning-tree portfast edge')
    print(' no shut')
    print('end')
    print()
    print(sec_sw+':')
    print()
    print('interface GigabitEthernet4/'+sec_port)
    print(' description '+loc.row+'-'+loc.rack+'-'+loc.slot+'-'+typeDict[type][2]+' '+alloc+' server - '+sid)
    print(' switchport')
    print(' switchport access vlan '+str(vlan))
    if pri_or_sec == 'pri':
        print(' switchport mode access')
    else:
        print(' private-vlan host-association 11 '+str(vlan))
        print(' switchport mode private-vlan host')
    print(' load-interval 30')
    print(' speed '+speed)
    print(' '+duplex)
    print(' spanning-tree portfast edge')
    print(' no shut')
    print('end')
    print()



