#!/usr/bin/env python3
# flexcabling.py

import flexcablingiad
import flexcablingsjc

def main():
    while True:
        try:
            site = input('Please select a site (iad/sjc): ').strip().lower()
            if not site in ['iad','sjc']:
                print('ERROR: INVALID DATA\n')
            else:
                break
        except ValueError:
            print('ERROR: INVALID DATA\n')
    if site == 'iad':
        flexcablingiad.main()
    else:
        flexcablingsjc.main()
if __name__ == '__main__':
    main()
