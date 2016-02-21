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
from flexresources import ask_symmetric_or_not,choose_switchports_HA,choose_flexports_SJC_HA
from flexresources import print_results_SJC_HA,ask_more

def main():
    # Prompt for username, password, and alloccode-depth (alloc)
    [username,password,alloc] = getUPA2()
    
    # Prompt for a VLAN
    vlan = getVLAN2()

    more = 'y'
    while more == 'y':
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
            symmetric = ask_symmetric_or_not()
            
            [port1,port2] = choose_switchports_HA(SW1,SW2,symmetric)
            
            [prim_flexport,sec_flexport,
             idf_port,prim_idf_num,sec_idf_num,
             prim_sw,sec_sw,
             prim_port,sec_port] = choose_flexports_SJC_HA(trace,loc,pri_or_sec,
                                                           priSW,pr2SW,secSW,
                                                           se2SW,port1,port2)
            
            print_results_SJC_HA(sid,loc,typeDict,type,spd,
                                 prim_flexport,prim_idf_num,u_num,
                                 idf_port,prim_sw,prim_port,
                                 sec_flexport,sec_idf_num,sec_sw,sec_port,
                                 alloc,vlan,pri_or_sec,speed,duplex)

        more = ask_more()

if __name__ == '__main__':
    main()
