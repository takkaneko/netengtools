#!/usr/bin/env python3
# backup.py
# Collects a list of sh run outputs from selected devices

import re
import time
import pexpect
from pexpect import EOF
from pexpect import TIMEOUT
from pexpect import ExceptionPexpect
from device_lists import ALL_NW_DEVICES,ALL_NW_DEVICES_IAD,ALL_NW_DEVICES_SJC
from device_lists import NX_OS_IAD,ASA_IAD,IOS_IAD,IOS_XE_IAD,IOS_XR_IAD
from device_lists import NX_OS_SJC,ASA_SJC,IOS_SJC,IOS_XE_SJC,IOS_XR_SJC
from device_lists import MULTICONTEXT_ASA

def choose_option():
    print('*********************************')
    print('NETWORK DEVICE CONFIG BACKUP TOOL')
    print('*********************************')
    print()
    print('Choose one of the following options:')
    print()
    print('1. Backup all Sterling NW devices')
    print('2. Backup all Denver NW devices')
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
            device = input().strip().lower()
        else:
            print('INVALID DEVICE NAME\n')
            device = input().strip().lower()
    return devices

def collectBackups(devices):
    success = 0
    failure = 0
    failed_devices = []
    for device in devices:
        # use pexpect to pull out config dump from device
        print('\nCollecting backup from '+device+'...')
        username = 'i853942'
        password = 'H@rtsdale10530!'
        if device in NX_OS_IAD + NX_OS_SJC:
            os = 'nxos'
        elif device in ASA_IAD + ASA_SJC:
            os = 'asa'
        elif device in IOS_IAD + IOS_SJC:
            os = 'ios'
        elif device in IOS_XE_IAD + IOS_XE_SJC:
            os = 'iosxe'
        else:
            os = 'iosxr'
        prompt = device+'(/admin|/pri/act|/sec/act)*#'
        term_zero = 'term pager line 0' if os == 'asa' else 'term len 0'
        term_reset = 'term pager line 24' if os == 'asa' else 'term len 24'
        CONTEXTS = ['A02I','A03R','A04P']
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
                child.expect(prompt,timeout=3)
            else:
                child.sendline(password)
                child.expect(prompt,timeout=5)
            print('Login successful')
            child.sendline(term_zero)
            child.expect(prompt,timeout=8)
            child.sendline('sh run')
            child.logfile = outfile
            child.expect(prompt,timeout=50)
            if device in MULTICONTEXT_ASA:
                # collect additional config dumps of individual contexts plus sys
                child.sendline('changeto sys')
                child.expect(device+'#',timeout=3)
                child.sendline('sh run')
                child.expect(device+'#',timeout=5)
                for context in CONTEXTS:
                    child.sendline('changeto context '+context)
                    #child.expect(device+'/'+context+'#',timeout=3)
                    child.expect(device+'/.+#',timeout=3)
                    child.sendline('sh run')
                    #child.expect(device+'/'+context+'#',timeout=6)
                    child.expect(device+'/.+#',timeout=50)
                child.sendline('changeto context admin')
                child.expect(prompt,timeout=3)
            # after collecting the output, reset terminal
            child.sendline(term_reset)
            child.expect(prompt,timeout=3)
            child.sendline('exit')
            print('Configs have been backed up for '+device)
            success += 1
        except (EOF,TIMEOUT,ExceptionPexpect):
            print('ERROR: Failed to backup configs of '+device)
            failure += 1
            failed_devices.append(device)
    print('\nBackup successful: '+str(success))
    print('Backup failure: '+str(failure))
    for failed_device in failed_devices:
        print('   '+failed_device)


if __name__ == '__main__':
    choice = choose_option()
    if choice == 1:
        devices = ALL_NW_DEVICES_IAD
    elif choice == 2:
        devices = ALL_NW_DEVICES_SJC
    elif choice == 3:
        devices = ALL_NW_DEVICES
    else:
        devices = get_devices()
    collectBackups(devices)



