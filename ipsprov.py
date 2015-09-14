#!/usr/bin/env python3
# ipsprov.py

# Use this option in case an IPS monitors two different 
# network devices where the devices can be either HA gears 
# or stand-alone gears.

# Also use in case an IPS aims at monitoring an HA *standby*
# gear (This is not common).

from hafwl2l3prov import getUPA
from locationcode import Loccode
from networksid import NWdevice

def getIPS():
    """
    Prompts to enter SID/location of IPS.
    """
    while True:
        try:
            ips = input("Enter the IPS ID: ").lower().strip()
            if NWdevice(ips).is_ips():
                ips = NWdevice(ips)
                break
            else:
                print("ERROR: SERVICE ID INVALID\n")
        except AttributeError:
            print('ERROR: SERVICE ID INVALID\n')
    while True:
        try:
            ipsloc = Loccode(input("Enter the location code of "+ips+": "))
            if ipsloc.is_NWloc():
                break
            else:
                print("ERROR: INVALID LOCATION\n")
        except AttributeError:
            print("ERROR: INVALID LOCATION\n")
    return [ips,ipsloc]

def getNWdevice(number,ipsloc):
    """
    Prompts to enter SIDs/speed/locations of a network device.
    nwdevice = newtwork device ID (firewall or loadbalancer)
    speed = 1000 or 100 (int)
    nwdeviceloc = network device location
    """
    # Service ID
    while True:
        try:
            nwdevice = input("Enter the service ID of a monitored device #"+str(number)+": ").lower().strip()
            if NWdevice(nwdevice).is_fw() or NWdevice(nwdevice).is_lb():
                nwdevice = NWdevice(nwdevice)
                break
            else:
                print("ERROR: SERVICE ID INVALID\n")
        except AttributeError:
            print('ERROR: SERVICE ID INVALID\n')
    # Speed
    while True:
        try:
            speed = input('Enter the interface speed (Mbps)[1000]: ').strip() or '1000'
            if not re.match(r"^10{2,3}$",speed):
                print('ERROR: DATA INVALID')
            else:
                print('OK - speed = '+speed+'Mbps')
                break
        except ValueError:
            print('ERROR: DATA INVALID')
    # Location
    while True:
        try:
            nwdeviceloc = Loccode(input("Enter the location code of "+nwdevice+": "))
            if nwdeviceloc.is_NWloc() and nwdeviceloc.srr == ipsloc.srr and nwdeviceloc.rack_noa == ipsloc.rack_noa and nwdeviceloc != ipsloc:
                print("OK")
                break
            elif nwdeviceloc == ipsloc:
                print("ERROR: The "+nwdevice+" and IPS cannot take the same slot!\n")
            elif not (nwdeviceloc.srr == ipsloc.srr and nwdeviceloc.rack_noa == ipsloc.rack_noa):
                print("ERROR: The "+nwdevice+" and IPS must be in the same rack\n")
            else:
                print("ERROR: INVALID LOCATION\n")
        except AttributeError:
            print("ERROR: SYNTAX INVALID\n")
    return [nwdevice,speed,nwdeviceloc]

def main():
    ##### Prompts to enter username, password, and allocation code:
    [username,password,alloccode] = getUPA()
    
    ##### Prompt to enter IPS SID and Location:
    [ips,ipsloc] = getIPS()
    
    ##### Prompt to enter the network device #1 SID and Location:
    [nwdevice1,speed1,nwdevice1loc] = getNWdevice(1,ipsloc)
    
    ##### Prompt to enter the device #1's monitored segment info:

    ##### Prompt to enter the network device #2 SID and Location:
    [nwdevice2,speed2,nwdevice2loc] = getNWdevice(2,ipsloc)
    
    ##### Prompt to enter the device #2's monitored segment info:
    
