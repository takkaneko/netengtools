#!/usr/bin/env python3
# backup.py
# Collects a list of sh run outputs from selected devices
# Create a separate device_lists.py and put your device lists in there
# The program must be able to reach all the interesting remote locations

import re
import time
import pexpect
from pexpect import EOF
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect
# Create a separate device_lists.py and put your device lists in there
from device_lists import ALL_NW_DEVICES,ALL_NW_DEVICES_DCA,ALL_NW_DEVICES_DCB

def choose_option():
    print('*********************************')
    print('NETWORK DEVICE CONFIG BACKUP TOOL')
    print('*********************************')
    print()
    print('Choose one of the following options:')
    print()
    print('1. Backup all Data Ctr A NW devices')
    print('2. Backup all Data Ctr B NW devices')
    print('3. Backup all NW devices')
    print('4. Backup a specific list of devices')
    print()
    while True:
        try:
            choice = int(input('Your choice: '))
            if choice in [1,2,3,4]:
                break
            else:
                print('ERROR: DATA OUT OF RANGE\n')
        except ValueError:
            print('ERROR: INVALID DATA\n')
    return choice

def get_devices():
    print('Type device names, one per line')
    print('When finished, type "f" and hit <Enter>.\n')
    devices = []
    device = input('Add device: ').strip().lower()
    while device != 'f':
        if device in ALL_NW_DEVICES:
            devices.append(device)
            device = input('Add device: ').strip().lower()
        else:
            print('INVALID DEVICE NAME\n')
            device = input('Add device: ').strip().lower()
    return devices

def collectBackups(devices):
    for device in devices:
        # use pexpect to pull out config dump from device
        print('\nCollecting backup from '+device+'...')
        username = '<EDIT_YOUR_USERNAME_HERE>'
        password = '<EDIT_YOUR_PASSWORD_HERE>'
        outfile = open(time.strftime("%Y-%m-%d")+'--'+device+'.txt', 'w')
        header = device + '('+ time.strftime("%Y-%m-%d") + '):\n'
        print(header, file=outfile)
        try:
            child = pexpect.spawnu('ssh '+username+'@'+device)
            i = child.expect(['Are you sure you want to continue connecting (yes/no)?','.*(P|p)assword:'],timeout=10)
            if i == 0:
                child.sendline('yes')
                child.expect('.*(P|p)assword:',timeout=3)
                child.sendline(password)
                child.expect(device+'#',timeout=3)
            else:
                child.sendline(password)
                child.expect(device+'#',timeout=3)
            print('Login successful')
            child.sendline('term len 0')
            child.expect(device+'#',timeout=3)
            child.sendline('sh run')
            child.logfile = outfile
            child.expect(device+'#',timeout=15)
            # after collecting the output, reset terminal
            child.sendline('term len 60')
            child.expect(device+'#',timeout=3)
            child.sendline('exit')
            print('Configs have been backed up for '+device)
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Failed to backup configs of '+device)
    
        # be sure to add narrative outputs as the process progresses
    # at the end, display a list of devices whose backup failed, if any.

if __name__ == '__main__':
    choice = choose_option()
    if choice == 1:
        devices = ALL_NW_DEVICES_DCA
    elif choice == 2:
        devices = ALL_NW_DEVICES_DCB
    elif choice == 3:
        devices = ALL_NW_DEVICES
    else:
        devices = get_devices()
    collectBackups(devices)



