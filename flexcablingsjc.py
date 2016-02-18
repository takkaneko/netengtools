#!/usr/bin/env python3
# flexcablingsjc.py

import re
import pexpect
from pexpect import EOF
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect
from locationcode import Loccode

def main():
    def swprfx(loc):
        loc = Loccode(loc)
        if loc.sr == 'sjc.c10':
            sw = 'sjc1'
        elif loc.sr == 'sjc.c4':
            sw = 'sjc4'
        elif loc.sr == 'sjc.c9':
            sw = 'sjc9'
        elif loc.sr == 'iad.c4':
            sw = 'iad4'
        return sw+loc.row.zfill(2)
    import getpass
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
    
    while True:
        try:
            sid = input('Enter a server ID: ').strip().lower()
            if not re.match(r"^[a-z]+\d{5}$",sid):
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
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
    if 4 <= int(loc.rack) <= 8:
        u_num = '5'
    elif 9 <= int(loc.rack) <= 12:
        u_num = '4'
    elif 13 <= int(loc.rack) <= 16:
        u_num = '3'
    else:
        u_num = '2'
    SWp1 = swprfx(loc)+'p1'
    SWp2 = swprfx(loc)+'p2'
    SWs1 = swprfx(loc)+'s1'
    SWs2 = swprfx(loc)+'s2'
    sjc_straight_racks = [4,6,9,11,13,15,17,20]
    sjc_reverse_racks = [5,8,10,12,14,16,18,21]
    if int(loc.rack) in sjc_straight_racks:
        trace = 'straight'
    else:
        trace = 'reversed'
    priSW = SWp1 if trace == 'straight' else SWp2
    pr2SW = SWp2 if trace == 'straight' else SWp1
    secSW = SWs1 if trace == 'straight' else SWs2
    se2SW = SWs2 if trace == 'straight' else SWs1
    #iloSW = SWs1 if int(loc.rack) <= 12 else SWs2 #iloSW not needed in this tool
    while True:
        try:
            vlan = int(input('Enter a VLAN ID: '))
            if vlan <= 0 or 4096 < vlan:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
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
    # dual...determines if the cabling is HA or not. 
    # custom_type...need to name the otherha/other cabling.
    # pri_or_sec...automatically set when obvious. manually claim one when the type is otherha/other.
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
    typeDict = {'hbeat': ('Heartbeat','hbt','hb2'),
          'vmotion': ('Vmotion','vmo','vm2'),
          'pri+': ('Add\'tl primarynet', 'pri','pr2'),
          'sec+': ('Add\'tl secnet','sec','se2'),
          'ilo': ('Routable ilo','ilo','ilo'),
          'otherha': (custom_type,'other','othr2'),
          'other': (custom_type,'other','other')}
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

    #Switch/port selections start here
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
    print()
    input('Hit Enter to check the switchport statuses on '+sw_pair+':')
    print()
    for switch in [SW1,SW2]:
        try:
            child = pexpect.spawnu('telnet '+switch+'.dn.net')
            child.expect('Username: ')
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

    # Case I: Single cabling type (ilo or other).
    
    if dual == 'n':
        while True:
            try:
                use_this_switch = input('Choose '+SW1+' or '+SW2+' to use this time: ').strip().lower()
                if not use_this_switch in [SW1,SW2]:
                    print('ERROR: DATA INVALID\n')
                else:
                    break
            except (ValueError,IndexError):
                print('ERROR: DATA INVALID\n')
        while True:
            try:
                port = input('Choose '+use_this_switch+' module 4 SWITCHPORT number to use this time (1 - 48): ').strip()
                if not 1<=int(port)<=48:
                    print('ERROR: DATA INVALID\n')
                else:
                    break
            except ValueError:
                print('ERROR: DATA INVALID\n')
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
        print(' switchport mode access')
        print(' load-interval 30')
        print(' speed '+speed)
        print(' '+duplex)
        print(' spanning-tree portfast edge')
        print(' no shut')
        print('end')
        print()
    
    # Case II: Dual cabling type (hbeat, vmotion, pri+, sec+, or otherha).
    
    else:
        while True:
            try:
                symmetric = input('Symmetric cabling (switchports)? [Y/n]: ').strip().lower()[0]
                if not symmetric in ['y','n']:
                    print('ERROR: DATA INVALID\n')
                else:
                    break
            except (ValueError,IndexError):
                print('ERROR: DATA INVALID\n')
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
        print(' switchport mode access')
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
        print(' switchport mode access')
        print(' load-interval 30')
        print(' speed '+speed)
        print(' '+duplex)
        print(' spanning-tree portfast edge')
        print(' no shut')
        print('end')
        print()

if __name__ == '__main__':
    main()
