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



##################################
# FUNCTIONS THAT ARE ONLY FOR SJC:
##################################

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







