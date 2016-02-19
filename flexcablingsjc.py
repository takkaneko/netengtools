#!/usr/bin/env python3
# flexcablingsjc.py

import re
import pexpect
from pexpect import EOF,TIMEOUT,ExceptionPexpect
from locationcode import Loccode
from flexresources import getUPA2,getVLAN2,getSID,os_and_speed,getLOC_SJC,idf_U_number_SJC
from flexresources import determine_trace_SJC,identify_switches,identify_switch_roles
from flexresources import get_cabling_type,identify_cabling_attributes,typeDictionary
from flexresources import summaryView,switch_pair,check_swport_usage,choose_sw1_or_sw2
from flexresources import choose_switchport,choose_flexport_SJC,print_results_SJC

def main():
    # Prompt for username, password, and alloccode-depth (alloc)
    [username,password,alloc] = getUPA2()
    
    # Prompt for a VLAN
    vlan = getVLAN2()
    
    # Prompt for a server ID
    sid = getSID()
    
    # Determine OS type, link settings
    [os,negotiate,speed,duplex,spd] = os_and_speed(sid)

    # Prompt for a valid location code (loc)
    loc = getLOC_SJC()
    
    # U number (as a string!) of the patch panel in the IDF racks 
    # (Will be used in cabling instructions)
    u_num = idf_U_number_SJC(loc)
    
    [SWp1,SWp2,SWs1,SWs2] = identify_switches(loc)
    
    # trace is either 'straight' or 'reversed'
    trace = determine_trace_SJC(loc)
    
    [priSW,pr2SW,secSW,se2SW] = identify_switch_roles(trace,SWp1,SWp2,SWs1,SWs2)

    # Prompt for a cabling type
    type = get_cabling_type()
    
    # Three key attributes are determined by the selection of cabling type done above
    [dual,custom_type,pri_or_sec] = identify_cabling_attributes(type)
    
    typeDict = typeDictionary(custom_type)
    
    summaryView(alloc,sid,os,negotiate,loc,trace,priSW,
                pr2SW,secSW,se2SW,vlan,type,dual,custom_type,pri_or_sec)

    # Switch/port selections start here
    # SW1 is p1 or s1
    # SW2 is p2 or s2
    [sw_pair,SW1,SW2] = switch_pair(type,pri_or_sec,SWp1,SWp2,SWs1,SWs2)
    
    # Shows outputs of sh int status mod 4 from SW1 then from SW2
    check_swport_usage(sw_pair,SW1,SW2,username,password)

    # Case I: Single cabling type (ilo or other).
    
    if dual == 'n':
        # ask user to pick either SW1 or SW2 for this flex cabling
        use_this_switch = choose_sw1_or_sw2(SW1,SW2)
        
        # ask user to pick a switchport - non-HA
        port = choose_switchport(use_this_switch)
        
        # ask user to pick a flexport - non-HA
        [flexport,idf_port,idf_num] = choose_flexport_SJC(use_this_switch,SW1,loc)
        
        # Outputs, non-HA
        print_results_SJC(sid,loc,spd,type,typeDict,flexport,idf_num,u_num,idf_port,
                          use_this_switch,port,alloc,vlan,pri_or_sec,speed,duplex)
    
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

if __name__ == '__main__':
    main()
