#!/usr/bin/env python3
# boreasprov.py

import hafwl2l3prov
import halbl2l3prov

def main():
    title ='\n*********************************\n'
    title += 'BOREAS NETWORK PROVISIONING SUITE\n'
    title += '*********************************\n\n'
    title += 'Please select your provisioning task from the following menus:\n'
    print(title)
    options =  '1. HA firewall (CP IP390/560 series or ASA5500 series)\n'
    options += '2. Stand-alone firewall (UTM series or ASA5500 series)\n'
    options += '3. HA Alteon4408\n'
    options += '4. Stand-alone Alteon4408\n'
    options += '5. IPS only (when monitoring multiple devices)\n'
    print(options)
    while True:
        try:
            choice = int(input('Type your selection then hit Enter: '))
            if 1 <= choice <=5:
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
        fwprov.main()
    if choice == 3:
        print('Starting HA Alteon4408 provisioning...\n')
        halbl2l3prov.main()
    if choice == 4:
        print('Starting stand-alone Alteon4408 provisioning...\n')
        lbprov.main()
    if choice == 5:
        print('Starting IPS provisioning...\n')
        ipsprov.main()
        
    
if __name__ == '__main__':
    main()
