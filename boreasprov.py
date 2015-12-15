#!/usr/bin/env python3
# boreasprov.py

import hafwl2l3prov
import fwl2l3prov
import halbl2l3prov
import lbl2l3prov
import ipsprov
import hafwiloprov
import fwiloprov

def main():
    title ='\n****************************************\n'
    title += 'BOREAS NETWORK DEVICE PROVISIONING SUITE\n'
    title += '****************************************\n\n'
    title += 'Please select your provisioning task from the following menus:\n'
    print(title)
    options =  '1. HA firewall (CheckPoint or ASA5500 series)\n'
    options += '2. Stand-alone firewall (CheckPoint or ASA5500 series)\n'
    options += '3. HA Alteon4408\n'
    options += '4. Stand-alone Alteon4408\n'
    options += '5. IPS only (To monitor multiple devices or an HA *standby*)\n'
    options += '6. HA firewall SecNet iLO segment (Not common)\n'
    options += '7. Stand-alone firewall SecNet iLO segment (Not common)\n'
    print(options)
    while True:
        try:
            choice = int(input('Type your selection then hit Enter: '))
            if 1 <= choice <=7:
                break
            else:
                print('ERROR: DATA OUT OF RANGE\n')
        except ValueError:
            print('ERROR: INVALID DATA PROVIDED\n')

    if choice == 1:
        print('Starting HA firewall provisioning...\n')
        hafwl2l3prov.main()
    if choice == 2:
        print('Starting stand-alone firewall provisioning...\n')
        fwl2l3prov.main()
    if choice == 3:
        print('Starting HA Alteon4408 provisioning...\n')
        halbl2l3prov.main()
    if choice == 4:
        print('Starting stand-alone Alteon4408 provisioning...\n')
        lbl2l3prov.main()
    if choice == 5:
        print('Starting IPS provisioning...\n')
        ipsprov.main()
    if choice == 6:
        print('Starting HA firewall SecNet iLO provisioning...\n')
        hafwiloprov.main()
    if choice == 7:
        print('Starting stand-alone firewall SecNet iLO provisioning...\n')
        fwiloprov.main()
        
    
if __name__ == '__main__':
    main()
