#!/usr/bin/env python3
# hafwprov.py

import re
import getpass

class Loccode(str):
    """
    A Loccode is a string object such as 'iad.c4.11.3a.11' that can be broken down into
    the following specific subcodes: site, room, row, rack, slot. Create a Loccode object
    in the following manner:

    loc = Loccode('iad.c4.11.3a.11')

    This gives you a convenience of quickly extracting individual subcodes. For example:

    >>> loc.row
    '11'
    >>> loc.site
    'iad'
    >>> loc.srr
    'iad.c4.11'
    """
    def __init__(self,loc):
        p = re.compile(r"^(((sjc|iad)+\.+(c4|c9|c10)+\.+(\d{1,2}))+\.+(\d{1,2}a{0,1}))+\.+(\d{1,2})$",re.IGNORECASE)
        loc = loc.strip()
        m = p.match(loc)
        site = m.group(3)
        self.site = site
        room = m.group(4)
        self.room = room
        row = m.group(5)
        self.row = row
        rack = m.group(6)
        self.rack = rack
        rack_noa = rack.strip('a')
        self.rack_noa = rack_noa
        slot = m.group(7)
        self.slot = slot
        srr = m.group(2)
        self.srr = srr    # srr = site.room.row (Useful sometimes)
        srrr = m.group(1)
        self.srrr = srrr  # srrr = site.room.row.rack (Yes also useful sometimes)
        p1 = re.compile(r"^((sjc|iad)+\.+(c4|c9|c10))+\.+((\d{1,2})+\.+((\d{1,2}a{0,1})+\.+(\d{1,2})))$",re.IGNORECASE)
        m1 = p1.match(loc)
        rs = m1.group(6)
        self.rs = rs      # rs = rack.slot (This is essential!)
        rrs = m1.group(4)
        self.rrs = rrs
        sr = m1.group(1)
        self.sr = sr

    def is_masterloc(self):
        """
        Boolean checker to see if the location is valid for a *MASTER* FW/LB.
        """
        site = self.site
        room = self.room
        row = int(self.row)
        rack = self.rack
        slot = int(self.slot)
        srr = self.srr
        srrr = self.srrr
        rs = self.rs
        rack_noa = self.rack_noa
        if site == 'iad':
            nw_rs = ('3.1','3.2','3.3','3.4','3.5','3.6','3.7','3.8',
                     '3.9','3a.9','3.10','3a.10','3.11','3a.11','3.12','3a.12',
                     #'3.13','3a.13','3.14','3a.14','3.15','3a.15','3.16','3a.16',
                     #'3.17','3a.17','3.18','3a.18','3.19','3a.19','3.20','3a.20',
                     #'12.1','12.2','12.3','12.4','12.5','12.6','12.7','12.8',
                     #'12.9','12a.9','12.10','12a.10','12.11','12a.11','12.12','12a.12',
                     '12.13','12a.13','12.14','12a.14','12.15','12a.15','12.16','12a.16',
                     '12.17','12a.17','12.18','12a.18','12.19','12a.19','12.20','12a.20')
        else:
            nw_rs = ('3.1', '3a.1', '3.2', '3a.2', '3.3', '3a.3', '3.4', '3a.4', 
                     '3.5', '3a.5', '3.6', '3a.6', '3.7', '3a.7', '3.8', '3a.8',
                     #'3.9', '3a.9', '3.10', '3a.10', '3.11', '3a.11', '3.12', '3a.12',
                     #'3.13', '3a.13', '3.14', '3a.14', '3.15', '3a.15', '3.16', '3a.16',
                     #'22.1', '22a.1', '22.2', '22a.2', '22.3', '22a.3', '22.4', '22a.4',
                     #'22.5', '22a.5', '22.6', '22a.6', '22.7', '22a.7', '22.8', '22a.8',
                     '22.9', '22a.9', '22.10', '22a.10', '22.11', '22a.11', '22.12', '22a.12',
                     '22.13', '22a.13', '22.14', '22a.14', '22.15', '22a.15', '22.16', '22a.16')

        if site == 'iad':
            return room == 'c4' and (row <=4 or row == 11) and nw_rs.__contains__(rs)

        else:
            rr = [('c10',row <= 2),
                  ('c9',row <= 4),
                  ('c4',3 <= row <= 4)]
            for rm,rw in rr:
                if room == rm:
                    return rw and nw_rs.__contains__(rs)

    def is_NWloc(self):
        """
        Boolean checker to see if the location is valid for a network device (Either master or standby).
        """
        site = self.site
        room = self.room
        row = int(self.row)
        rack = self.rack
        slot = int(self.slot)
        srr = self.srr
        srrr = self.srrr
        rs = self.rs
        rack_noa = self.rack_noa
        if site == 'iad':
            nw_rs = ('3.1','3.2','3.3','3.4','3.5','3.6','3.7','3.8',
                     '3.9','3a.9','3.10','3a.10','3.11','3a.11','3.12','3a.12',
                     '3.13','3a.13','3.14','3a.14','3.15','3a.15','3.16','3a.16',
                     '3.17','3a.17','3.18','3a.18','3.19','3a.19','3.20','3a.20',
                     '12.1','12.2','12.3','12.4','12.5','12.6','12.7','12.8',
                     '12.9','12a.9','12.10','12a.10','12.11','12a.11','12.12','12a.12',
                     '12.13','12a.13','12.14','12a.14','12.15','12a.15','12.16','12a.16',
                     '12.17','12a.17','12.18','12a.18','12.19','12a.19','12.20','12a.20')
        else:
            nw_rs = ('3.1', '3a.1', '3.2', '3a.2', '3.3', '3a.3', '3.4', '3a.4', 
                     '3.5', '3a.5', '3.6', '3a.6', '3.7', '3a.7', '3.8', '3a.8',
                     '3.9', '3a.9', '3.10', '3a.10', '3.11', '3a.11', '3.12', '3a.12',
                     '3.13', '3a.13', '3.14', '3a.14', '3.15', '3a.15', '3.16', '3a.16',
                     '22.1', '22a.1', '22.2', '22a.2', '22.3', '22a.3', '22.4', '22a.4',
                     '22.5', '22a.5', '22.6', '22a.6', '22.7', '22a.7', '22.8', '22a.8',
                     '22.9', '22a.9', '22.10', '22a.10', '22.11', '22a.11', '22.12', '22a.12',
                     '22.13', '22a.13', '22.14', '22a.14', '22.15', '22a.15', '22.16', '22a.16')

        if site == 'iad':
            return room == 'c4' and (row <=4 or row == 11) and nw_rs.__contains__(rs)

        else:
            rr = [('c10',row <= 2),
                  ('c9',row <= 4),
                  ('c4',3 <= row <= 4)]
            for rm,rw in rr:
                if room == rm:
                    return rw and nw_rs.__contains__(rs)

    def peerloc(self):
        """
        Returns the HA peer's location.
        Assumes that mloc is already validated with is_masterloc.
        In other words, peerloc itself doesn't confirm that mloc is a valid master location.
        """
        site = self.site
        room = self.room
        row = int(self.row)
        rack = self.rack
        slot = int(self.slot)
        srr = self.srr
        srrr = self.srrr
        rs = self.rs
        rack_noa = self.rack_noa
        p1 = re.compile(r"^3a{0,1}$")
        if p1.match(rack):
            if site == 'iad':
                srack = rack.replace('3','12')
            else:
                srack = rack.replace('3','22')
        else:
            if site == 'iad':
                srack = rack.replace('12','3')
            else:
                srack = rack.replace('22','3')
        sloc = srr+'.'+srack+'.'+str(slot)
        sloc = Loccode(sloc)
        return sloc

    def findmod(self):
        """
        Simply tells if the device in location loc is connected to module 5 or module 6
        of the directly connected distribution switch.
        Works for any legitimate locations, not just network device locations.
        Returns either '5' or '6' - remember these are strings!
        """
        site = self.site
        room = self.room
        row = int(self.row)
        rack = self.rack
        slot = int(self.slot)
        srr = self.srr
        srrr = self.srrr
        rs = self.rs
        rack_noa = self.rack_noa
        ss = [('iad',12),
              ('sjc',8)]
        for st,sl in ss:
            if site == st:
                if slot <= sl:
                    mod = '5'
                else:
                    mod = '6'
        return mod

    def findsw(self):
        """
        Returns the directly connected distribution switch. Works for any legitimate locations,
        not just network device locations.
        """
        site = self.site
        room = self.room
        row = int(self.row)
        rack = self.rack
        slot = int(self.slot)
        srr = self.srr
        srrr = self.srrr
        rs = self.rs
        rack_noa = self.rack_noa
        if room == 'c4':
            num = 400
        elif room == 'c9':
            num = 900
        else:
            num = 100
        mswitch = site+str(num+row)+'p1'
        sswitch = site+str(num+row)+'p2'
        # mod is 5 or 6 depending on the slot height!
        p3 = re.compile(r"^3a{0,1}$")
        p12 = re.compile(r"^12a{0,1}$")
        p22 = re.compile(r"^22a{0,1}$")
        if site == 'iad':
            if (p3.match(rack) and slot <= 12) or (p12.match(rack) and 13 <= slot):
                switch = mswitch
            else:
                switch = sswitch
        else:
            if (p3.match(rack) and slot <= 8) or (p22.match(rack) and 9 <=slot):
                switch = mswitch
            else:
                switch = sswitch
        return switch

    def findfrport(self):
        """
        Returns the front switchport assigned to the network device location.
        """
        site = self.site
        room = self.room
        row = int(self.row)
        rack = self.rack
        slot = int(self.slot)
        srr = self.srr
        srrr = self.srrr
        rs = self.rs
        rack_noa = self.rack_noa

        if site == 'iad':
            nw_rs = ('3.1','3.2','3.3','3.4','3.5','3.6','3.7','3.8',
                     '3.9','3a.9','3.10','3a.10','3.11','3a.11','3.12','3a.12',
                     '3.13','3a.13','3.14','3a.14','3.15','3a.15','3.16','3a.16',
                     '3.17','3a.17','3.18','3a.18','3.19','3a.19','3.20','3a.20',
                     '12.1','12.2','12.3','12.4','12.5','12.6','12.7','12.8',
                     '12.9','12a.9','12.10','12a.10','12.11','12a.11','12.12','12a.12',
                     '12.13','12a.13','12.14','12a.14','12.15','12a.15','12.16','12a.16',
                     '12.17','12a.17','12.18','12a.18','12.19','12a.19','12.20','12a.20')
        else:
            nw_rs = ('3.1', '3a.1', '3.2', '3a.2', '3.3', '3a.3', '3.4', '3a.4', 
                     '3.5', '3a.5', '3.6', '3a.6', '3.7', '3a.7', '3.8', '3a.8',
                     '3.9', '3a.9', '3.10', '3a.10', '3.11', '3a.11', '3.12', '3a.12',
                     '3.13', '3a.13', '3.14', '3a.14', '3.15', '3a.15', '3.16', '3a.16',
                     '22.1', '22a.1', '22.2', '22a.2', '22.3', '22a.3', '22.4', '22a.4',
                     '22.5', '22a.5', '22.6', '22a.6', '22.7', '22a.7', '22.8', '22a.8',
                     '22.9', '22a.9', '22.10', '22a.10', '22.11', '22a.11', '22.12', '22a.12',
                     '22.13', '22a.13', '22.14', '22a.14', '22.15', '22a.15', '22.16', '22a.16')
        frontport = nw_rs.index(rs)%16+1
        frontif = 'gi'+self.findmod()+'/'+str(frontport)
        return frontif

    def findbkport(self):
        """
        Returns the back switchport assigned to the network device location.
        """
        site = self.site
        room = self.room
        row = int(self.row)
        rack = self.rack
        slot = int(self.slot)
        srr = self.srr
        srrr = self.srrr
        rs = self.rs
        rack_noa = self.rack_noa

        if site == 'iad':
            nw_rs = ('3.1','3.2','3.3','3.4','3.5','3.6','3.7','3.8',
                     '3.9','3a.9','3.10','3a.10','3.11','3a.11','3.12','3a.12',
                     '3.13','3a.13','3.14','3a.14','3.15','3a.15','3.16','3a.16',
                     '3.17','3a.17','3.18','3a.18','3.19','3a.19','3.20','3a.20',
                     '12.1','12.2','12.3','12.4','12.5','12.6','12.7','12.8',
                     '12.9','12a.9','12.10','12a.10','12.11','12a.11','12.12','12a.12',
                     '12.13','12a.13','12.14','12a.14','12.15','12a.15','12.16','12a.16',
                     '12.17','12a.17','12.18','12a.18','12.19','12a.19','12.20','12a.20')
        else:
            nw_rs = ('3.1', '3a.1', '3.2', '3a.2', '3.3', '3a.3', '3.4', '3a.4', 
                     '3.5', '3a.5', '3.6', '3a.6', '3.7', '3a.7', '3.8', '3a.8',
                     '3.9', '3a.9', '3.10', '3a.10', '3.11', '3a.11', '3.12', '3a.12',
                     '3.13', '3a.13', '3.14', '3a.14', '3.15', '3a.15', '3.16', '3a.16',
                     '22.1', '22a.1', '22.2', '22a.2', '22.3', '22a.3', '22.4', '22a.4',
                     '22.5', '22a.5', '22.6', '22a.6', '22.7', '22a.7', '22.8', '22a.8',
                     '22.9', '22a.9', '22.10', '22a.10', '22.11', '22a.11', '22.12', '22a.12',
                     '22.13', '22a.13', '22.14', '22a.14', '22.15', '22a.15', '22.16', '22a.16')
        backport = nw_rs.index(rs)%16+17
        backif = 'gi'+self.findmod()+'/'+str(backport)
        return backif


def validateSIDFormat(devicename):
    """
    Basic format check of a service ID.
    """
    pfw = re.compile(r"^([a-z]+)+(\d+)+([a-z]+)+(\d{5})$")
    plb = re.compile(r"^(alteonha)+(m|s)+(slb)+\d{5}$")
    pother = re.compile(r"^(\w+)+\d{4,5}$")
    if re.compile(r"^fw$").match(devicename):
        return pfw.match(devicename)
    elif re.compile(r"^slb$").match(devicename):
        return plb.match(devicename)
    else:
        return pother.match(devicename)

def stdbyPeer(devicename):
    """
    Generates a service ID of an HA peer standby device.
    """
    peer = devicename.replace('hamfw','hasfw').replace('hamslb','hasslb')
    return peer


def main():
    username = ''
    while username == '':
        username = input("Enter your tacacs username: ")
    password = ''
    while password == '':
        password = getpass.getpass(prompt='Enter your tacacs password: ',stream=None)
    print('OK')
    alLoccode = ''
    while alLoccode == '':
        alLoccode = input('Enter an allocation code: ').lower().strip()
    print('OK')
    mfw = ''
    while mfw == '':
        mfw = input("Enter the master firewall ID: ")
        mfw = mfw.strip()
        if validateSIDFormat(mfw):
            break
        else:
            print("ERROR: INVALID SID FORMAT\n")
            mfw = ''
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
    sfw = stdbyPeer(mfw)
    while True:
        try:
            mfwloc = Loccode(input("Enter the location code of "+mfw+": "))
            if mfwloc.is_masterloc():
                break
            else:
                print("ERROR: INVALID LOCATION FOR MASTER\n")
        except AttributeError:
            print("ERROR: INVALID LOCATION\n")
    sfwloc = mfwloc.peerloc()
    print('OK')
    print("The location of secondary "+sfw+" is {0}.".format(sfwloc))
    ips = ''
    while ips =='':
        ips = input("Enter an IPS ID that goes to the master segment, or type 'none': ")
        ips = ips.strip().replace("'","")
        if ips == 'none' or validateSIDFormat(ips):
            break
        else:
            print('ERROR: INVALID SID FORMAT\n')
            ips = ''
    if ips != 'none':
        while True:
            try:
                ipsloc = Loccode(input("Enter the location code of "+ips+": "))
                if ipsloc.is_NWloc() and (mfwloc.srr == ipsloc.srr and mfwloc.rack_noa == ipsloc.rack_noa) and mfwloc != ipsloc:
                    print("OK")
                    break
                elif mfwloc == ipsloc:
                    print("ERROR: Master firewall and IPS cannot take the same slot!\n")
                elif not (mfwloc.srr == ipsloc.srr and mfwloc.rack_noa == ipsloc.rack_noa):
                    print("ERROR: Master firewall and IPS must be in the same rack\n")
                else:
                    print("ERROR: INVALID LOCATION\n")
            except AttributeError:
                print("ERROR: SYNTAX INVALID\n")
    else:
        print("OK no IPS!")
    print()
    print("The standard front/back switchports of the devices that you entered:\n\n")
    print(mfw+' ('+mfwloc+'):')
    print(' Front: '+mfwloc.findsw()+' '+mfwloc.findfrport())
    print(' Back:  '+mfwloc.findsw()+' '+mfwloc.findbkport())
    print()
    print(sfw+' ('+sfwloc+'):')
    print(' Front: '+sfwloc.findsw()+' '+sfwloc.findfrport())
    print(' Back:  '+sfwloc.findsw()+' '+sfwloc.findbkport())
    print()
    if ips != 'none':
        print(ips+' ('+ipsloc+'):')
        print(' Front: '+ipsloc.findsw()+' '+ipsloc.findfrport())
        print(' Back:  '+ipsloc.findsw()+' '+ipsloc.findbkport())

    ######################### FRONT SEGMENT VLAN #########################
    while True:
        try:
            frontVlan = int(input('\nEnter the VLAN ID of the firewall front: '))
            if frontVlan <= 0 or 4096 < frontVlan:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID')
    ###################### FRONT SEGMENT DEPTHCODE ######################
    while True:
        try:
            frontdepth = input('\nEnter the depth code of the firewall front [0001]: ').strip() or '0001'
            if not re.match(r"^0\d{3}$",frontdepth):
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    ######################################################################

    print('OK\nNow let\'s define firewall back segments, one by one.\n')

    ##################### STANDARD BACK SEGMENT NAME #####################
    backName = ''
    while backName == '':
        backName = input('Enter the friendly name of the standard back segment: ').strip()
    ##################### STANDARD BACK SEGMENT VLAN #####################
    while True:
        try:
            backVlan = int(input('Enter the VLAN ID of '+backName+': '))
            if frontVlan == backVlan:
                print('ERROR: '+backName+' VLAN cannot be the same as the front VLAN!\n')
            elif backVlan <= 0 or 4096 < backVlan:
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    ####################### BACK SEGMENT DEPTHCODE #######################
    while True:
        try:
            backdepth = input('\nEnter the depth code of the firewall back [0101]: ').strip() or '0101'
            if not re.match(r"^0\d{3}$",backdepth):
                print('ERROR: DATA INVALID\n')
            else:
                break
        except ValueError:
            print('ERROR: DATA INVALID\n')
    ######################### STANDARD BACK IPS QUESTION #########################
    monitored = 0
    if ips != 'none':
        while True:
            try:
                ans1 = input('Monitored by IPS? [y/N]: ').lower().strip()
                if ans1[0] == 'y':
                    monitored += 1
                    print('OK - Set to be monitored by IPS!')
                    break
                elif ans1[0] == 'n':
                    print('OK')
                    break
                else:
                    print('ERROR: INVALID ANSWER\n')
            except IndexError:
                print('ERROR: DATA INVALID\n')
    else:
        ans1 = 'n'
    ##################### LOOP - BACK SEGMENTS ADDITIONS #########################
    Ports = [1,16]         # FW segment ports. First two for front & back (1,16) are fake.
    Segments = ['fr',backName] # FW segment names
    SegmentsL = ['fr',backName.lower()] # FW segment names with all chars lowered.
    Sniff = ['n',ans1[0]]
    Vlans = [frontVlan,backVlan]    # FW vlans. ipsmgtVlan not included.
    Depths = [frontdepth,backdepth]
    ########## SUB-ROUTINE 'ADD?' ##########
    add = input('Add an additional back segment? [y/N]: ').lower().strip()
    while True:
        try:
            if add[0] == 'y':
                break
            elif add[0] == 'n' or add == '':
                print('OK - no additional segment')
                break
            else:
                print('ERROR: INVALID ANSWER\n')
                add = input('Add an additional back segment? [y/N]: ').lower().strip()
        except IndexError:
            print('ERROR: INVALID ANSWER\n')
            add = input('Add an additional back segment? [y/N]: ').lower().strip()
    ############# SUB-ROUTINE: CHOOSE PORT ###########
    while add[0] == 'y':
        try:
            auxport = int(input('Pick the next available port number (>=33) on mod '
                                +mfwloc.findmod()+' of '+mfwloc.findsw()+'-'+sfwloc.findsw()+': '))
            if not 33 <= auxport <= 48:
                print('ERROR: INVALID PORT NUMBER\n')
            elif Ports.__contains__(auxport):
                print('ERROR: The selected port number is already taken!\n')
            else:
                print('OK')
                Ports.append(auxport)
                ############# SUB-ROUTINE: CREATE SEGMENT NAME ###########
                while True:
                    try:
                        auxsegment = input('Enter the friendly name of this segment: ').strip()
                        auxsegmentl = auxsegment.lower()
                        if SegmentsL.__contains__(auxsegmentl):
                            print('ERROR: '+auxsegment+' already exists!\n')
                        elif auxsegment == '':
                            print('ERROR: DATA INVALID\n')                       
                        else:
                            Segments.append(auxsegment)
                            SegmentsL.append(auxsegmentl)
                            break
                    except ValueError:
                        print('ERROR: DATA INVALID\n')
                ############# SUB-ROUTINE: CHOOSE VLAN ###########
                while True:
                    try:
                        auxvlan = int(input('Enter the VLAN ID of '+auxsegment+': '))
                        if Vlans.__contains__(auxvlan):
                            print('ERROR: The selected VLAN is already taken!\n')
                        elif auxvlan <= 0 or 4096 < auxvlan:
                            print('ERROR: DATA INVALID\n')
                        else:
                            Vlans.append(auxvlan)
                            break
                    except ValueError:
                        print('ERROR: DATA INVALID\n')
                ############# SUB-ROUTINE: CHOOSE DEPTH CODE ###########
                while True:
                    try:
                        auxdepth = input('Enter the depth code of this back segment: ').strip()
                        if not re.match(r"^0\d{3}$",auxdepth):
                            print('ERROR: DATA INVALID\n')
                        elif Depths.__contains__(auxdepth):
                            print('ERROR: The depth code already exists!\n')
                        else:
                            Depths.append(auxdepth)
                            break
                    except ValueError:
                        print('ERROR: DATA INVALID\n')
                ######################### IPS OPTION #########################
                while ips != 'none' and monitored < 2:
                    try:
                        ans2 = input('Monitored by IPS? [y/N]: ').lower().strip()
                        if ans2[0] == 'y':
                            monitored += 1
                            Sniff.append('y')
                            print('OK - Set to be monitored by IPS!')
                            break
                        elif ans2[0] == 'n':
                            Sniff.append('n')
                            print('OK')
                            break
                        else:
                            print('ERROR: INVALID ANSWER\n')
                    except IndexError:
                        print('ERROR: DATA INVALID\n')
                if ips == 'none' or monitored == 2:
                    Sniff.append('n')
                ###################### END OF IPS OPTION ######################
                ########## SUB-ROUTINE 'ADD?' ##########
                add = input('Add an additional back segment? [y/N]: ').lower().strip()
                while True:
                    try:
                        if add[0] == 'y':
                            break
                        elif add[0] == 'n' or add == '':
                            print('OK - no additional segment\n')
                            break
                        else:
                            print('ERROR: INVALID ANSWER\n')
                            add = input('Add an additional back segment? [y/N]: ').lower().strip()
                    except IndexError:
                        print('ERROR: INVALID ANSWER\n')
                        add = input('Add an additional back segment? [y/N]: ').lower().strip()
                ############# END OF 'ADD?' ###########
        except ValueError:
            print('ERROR: DATA INVALID\n')
    ############################## END OF LOOP #################################
    ############################ IPS MANAGEMENT VLAN ############################
    if ips != 'none':
        print('\nNow choose the IPS management VLAN.\n'
              +'It can be any one of the VLANs that you allocated to this customer.\n'
              +'However, try avoiding a VLAN that is widely exposed to the Internet.')
        while True:
            try:
                ipsmgtVlan = int(input('Enter the VLAN ID of IPS mgmt: '))
                if ipsmgtVlan == frontVlan:
                    print('WARNING: FIREWALL FRONT VLAN MAY BE EXPOSED TO THE INTERNET!\n')
                    ans = input('ARE YOU SURE TO PROCEED? [y/N]: ').lower().strip()
                    if ans[0] == 'y':
                        print('OK - IPS mgmt VLAN is set to '+str(ipsmgtVlan))
                        break
                    elif ans[0] == 'n' or ans[0] == '':
                        pass
                    else:
                        print('ERROR: INVALID ANSWER\n')
                elif ipsmgtVlan <= 0 or 4096 < ipsmgtVlan:
                    print('ERROR: DATA INVALID\n')
                else:
                    print('OK')
                    break
            except (ValueError, IndexError):
                print('ERROR: DATA INVALID\n')
    ######################### IPS MANAGEMENT DEPTH CODE #########################
    if ips != 'none':
        if Vlans.__contains__(ipsmgtVlan):
            idx = Vlans.index(ipsmgtVlan)
            ipsmgtDepth = Depths[idx]
        else:
            while True:
                try:
                    ipsmgtDepth = input('Enter the depth code of VLAN '+str(ipsmgtVlan)+': ').strip()
                    if not re.match(r"^0\d{3}$",ipsmgtDepth):
                        print('ERROR: DATA INVALID\n')
                    elif Depths.__contains__(ipsmgtDepth):
                        print('ERROR: The depth code already exists!\n')
                    else:
                        print('OK')
                        break
                except ValueError:
                    print('ERROR: DATA INVALID\n')

    print('\nThe rest will generate port configs, custom cabling info, allocation form, etc.\n')
    
    # back up port configs
    print('******************************************************')
    print('Use the following to collect switchport backup configs')
    print('******************************************************\n')
    
    backups = [(mfwloc,'5'),(sfwloc,'6')]
    for loc,mod in backups:
        backup = 'telnet '+loc.findsw()+'\n'
        backup += username+'\n'
        backup += password+'\n'
        backup += 'sh run int '+loc.findfrport()+'\n'
        backup += 'sh run int '+loc.findbkport()+'\n'
        for port in Ports[2:]:
            backup += 'sh run int gi'+loc.findmod()+'/'+str(port)+'\n'
        if ips != 'none' and ipsloc.findmod() == mod:
            backup += 'sh run int '+ipsloc.findfrport()+'\n'
            backup += 'sh run int '+ipsloc.findbkport()+'\n'
        backup += 'exit\n'
        print(backup)
    input('Hit Enter to view the new switchport configs.')
    print()
    # new port configs
    print('*************************************************')
    print('Use the following to apply new switchport configs')
    print('*************************************************\n')
    
    swconfigs = [(mfwloc,'m',mfw,'5'),(sfwloc,'s',sfw,'6')]
    for loc,role,sid,mod in swconfigs:
        swconf = 'telnet '+loc.findsw()+'\n'
        swconf += username+'\n'
        swconf += password+'\n'
        swconf += 'int '+loc.findfrport()+'\n'
        swconf += ' description '+loc.rrs.replace('.','-')+'-'+role+'fr '+alLoccode+'-'+Depths[0]+' '+sid+' front\n'
        swconf += ' switchport\n'
        swconf += ' switchport access vlan '+str(Vlans[0])+'\n'
        swconf += ' switchport mode access\n'
        swconf += ' speed 1000\n'
        swconf += ' duplex full\n'
        swconf += ' spanning-tree portfast edge\n'
        swconf += ' no shut\n'
        swconf += '!\n'
        swconf += 'int '+loc.findbkport()+'\n'
        swconf += ' description '+loc.rrs.replace('.','-')+'-'+role+'bk '+alLoccode+'-'+Depths[1]+' '+sid+' back\n'
        swconf += ' switchport\n'
        swconf += ' switchport access vlan '+str(Vlans[1])+'\n'
        swconf += ' switchport mode access\n'
        swconf += ' speed 1000\n'
        swconf += ' duplex full\n'
        swconf += ' spanning-tree portfast edge\n'
        swconf += ' no shut\n'
        swconf += '!\n'
        aux = 2
        for port in Ports[2:]:
            swconf += 'int gi'+loc.findmod()+'/'+str(port)+'\n'
            swconf += ' description '+loc.rrs.replace('.','-')+'-'+role+'b'+str(aux)+' '+alLoccode+'-'+Depths[aux]+' '+sid+' back'+str(aux)+'\n'
            swconf += ' switchport\n'
            swconf += ' switchport access vlan '+str(Vlans[aux])+'\n'
            swconf += ' switchport mode access\n'
            swconf += ' speed 1000\n'
            swconf += ' duplex full\n'
            swconf += ' spanning-tree portfast edge\n'
            swconf += ' no shut\n'
            swconf += '!\n'
            aux += 1
        if ips != 'none' and ipsloc.findmod() == mod:
            swconf += 'int '+ipsloc.findfrport()+'\n'
            swconf += ' description RESERVED: '+ipsloc.rrs.replace('.','-')+'-fr '+alLoccode+' '+ips+'\n'
            swconf += ' switchport\n'
            swconf += ' switchport access vlan 133\n'
            swconf += ' switchport mode access\n'
            swconf += ' spanning-tree portfast edge\n'
            swconf += ' shut\n'
            swconf += '!\n'
            swconf += 'int '+ipsloc.findbkport()+'\n'
            swconf += ' description '+ipsloc.rrs.replace('.','-')+'-bk '+alLoccode+'-'+ipsmgtDepth+' '+ips+' mgmt\n'
            swconf += ' switchport\n'
            swconf += ' switchport access vlan '+str(ipsmgtVlan)+'\n'
            swconf += ' switchport mode access\n'
            swconf += ' spanning-tree portfast edge\n'
            swconf += ' no shut\n!\n'
        swconf += ' end\n'
        print(swconf)
    input('Hit Enter to view the custom cabling information')
    print()
    # cabling instructions
    site = mfwloc.site
    rs = mfwloc.rs
    if site == 'iad':
        nw_rs = ('3.1','3.2','3.3','3.4','3.5','3.6','3.7','3.8',
                 '3.9','3a.9','3.10','3a.10','3.11','3a.11','3.12','3a.12',
                 '3.13','3a.13','3.14','3a.14','3.15','3a.15','3.16','3a.16',
                 '3.17','3a.17','3.18','3a.18','3.19','3a.19','3.20','3a.20',
                 '12.1','12.2','12.3','12.4','12.5','12.6','12.7','12.8',
                 '12.9','12a.9','12.10','12a.10','12.11','12a.11','12.12','12a.12',
                 '12.13','12a.13','12.14','12a.14','12.15','12a.15','12.16','12a.16',
                 '12.17','12a.17','12.18','12a.18','12.19','12a.19','12.20','12a.20')
    else:
        nw_rs = ('3.1', '3a.1', '3.2', '3a.2', '3.3', '3a.3', '3.4', '3a.4', 
                 '3.5', '3a.5', '3.6', '3a.6', '3.7', '3a.7', '3.8', '3a.8',
                 '3.9', '3a.9', '3.10', '3a.10', '3.11', '3a.11', '3.12', '3a.12',
                 '3.13', '3a.13', '3.14', '3a.14', '3.15', '3a.15', '3.16', '3a.16',
                 '22.1', '22a.1', '22.2', '22a.2', '22.3', '22a.3', '22.4', '22a.4',
                 '22.5', '22a.5', '22.6', '22a.6', '22.7', '22a.7', '22.8', '22a.8',
                 '22.9', '22a.9', '22.10', '22a.10', '22.11', '22a.11', '22.12', '22a.12',
                 '22.13', '22a.13', '22.14', '22a.14', '22.15', '22a.15', '22.16', '22a.16')
    
    if site == 'iad':
        (sync,bk,bks) = ('51','50','49')
    else:
        (sync,bk,bks) = ('44','43','42')
    nokiaPorts = ['eth-1','eth-2','eth-3','s1p1','s1p2','s1p3','s1p4','s2p1','s2p2','s2p3','s2p4'] # eth4 is reserved for sync
    asa25Ports = ['gi0/1','gi0/2','gi0/3','gi0/4','gi0/5','gi0/6'] # gi0/7 is for sync
    print('CUSTOM CABLING INFORMATION:')
    print('---------------------------\n')
    cabling = 'sysc:\n'
    x = nw_rs.index(rs)
    cabling += '  '+mfw+' eth-4 -> YELLOW XOVER -> U'+sync+' YELLOW PANEL p'+str(x+1 if x<=15 else x-31)+'\n'
    cabling += '  '+sfw+' eth-4 -> YELLOW STRAIGHT -> U'+sync+' YELLOW PANEL p'+str(x+1 if x<=15 else x-31)+'\n\n'
    cumulative = 0
    if Sniff[1] == 'y':
        cumulative += 1
        cabling += backName+':\n'
        cabling += '  '+mfw+' eth-2 -> GREEN XOVER -> '+ips+'port 1A\n'
        cabling += '  '+ips+' port 1B -> GREEN STRAIGHT -> U'+bk+' UPPER ORANGE PANEL p'+str(nw_rs.index(rs)%16+17)+'\n\n'
    auxII = 2
    for segment in Segments[2:]:
        cabling += segment+':\n'
        if Sniff[auxII] == 'y':
            cumulative += 1
            cabling += '  '+mfw+' '+nokiaPorts[auxII]+' -> GREEN XOVER -> '+ips+' port '+str('1A' if cumulative == 1 else '2C')+'\n'
            cabling += '  '+ips+' port '+str('1B' if cumulative == 1 else '2D')+' -> GREEN STRAIGHT -> U'+bk+' UPPER ORANGE PANEL p'+str(Ports[auxII])+'\n'
        else:
            cabling += '  '+mfw+' '+nokiaPorts[auxII]+' -> GREEN STRAIGHT -> U'+bk+' UPPER ORANGE PANEL p'+str(Ports[auxII])+'\n'
        cabling += '  '+sfw+' '+nokiaPorts[auxII]+' -> GREEN STRAIGHT -> U'+bks+' LOWER ORANGE PANEL p'+str(Ports[auxII])+'\n\n'
        auxII += 1
    print(cabling)
    input('Hit Enter to view the firewall allocation form')
    print()
    # firewall allocation form (without IP info)
    firewallForm = 'FIREWALL NETWORK INFORMATION:\n'
    firewallForm += '------------------------------\n\n'
    firewallForm += 'Allocation Code: '+alLoccode+'\n\n'
    firewallForm += 'Master Firewall ID:            '+mfw+'\n'
    firewallForm += 'Backup Firewall ID:            '+sfw+'\n'
    firewallForm += 'Master Rack/Console Loc.Code:  '+mfwloc+'\n'
    firewallForm += 'Backup Rack/Console Loc.Code:  '+sfwloc+'\n'
    firewallForm += 'Firewall Network Unit: Infra 4.0, equipment racks: '+mfwloc.row+'-'+mfwloc.rack_noa+', '+sfwloc.row+'-'+sfwloc.rack_noa+'\n\n'
    firewallForm += 'Firewalls Front (Network '+frontdepth+')\n\n'
    firewallForm += '  Physical Interface: '+nokiaPorts[0]+'\n\n'
    firewallForm += '  Firewall Front-VRRP Interface:   \n'
    firewallForm += '  Master Firewall Front Interface: \n'
    firewallForm += '  Backup Firewall Front Interface: \n\n'
    firewallForm += '  Default Gateway:  \n'
    firewallForm += '  Front Network:    \n'
    firewallForm += '  Front Netmask:    \n\n'
    firewallForm += '  Master Firewall Connection To (Row Agg Sw. ID): '+mfwloc.findsw()+'\n'
    firewallForm += '  Master Firewall Connection Port:                '+mfwloc.findfrport()+'\n\n'
    firewallForm += '  Backup Firewall Connection To (Row Agg Sw. ID): '+sfwloc.findsw()+'\n'
    firewallForm += '  Backup Firewall Connection Port:                '+sfwloc.findfrport()+'\n\n'
    firewallForm += '  SwitchPort Speed/Duplex set to:                 '+speed+'M/Full\n'
    firewallForm += '   (firewalls should be set to the same speed)\n'
    firewallForm += '  INFRA4.0 VLAN (Num/Label):   '+str(frontVlan)+'/'+mfwloc.room+'r'+str("%02d" % int(mfwloc.row))+'-'+alLoccode+'-'+frontdepth+'\n\n'
    firewallForm += 'Firewalls Backs:\n\n'
    firewallForm += '**'+backName+' (Network '+backdepth+')\n\n'
    firewallForm += '  Physical Interface: '+nokiaPorts[1]+'\n\n'
    firewallForm += '  Firewall Back-VRRP Interface:    (gateway for ???)\n'
    firewallForm += '  Master Firewall Back Interface: \n'
    firewallForm += '  Backup Firewall Back Interface: \n\n'
    firewallForm += '  Back Network:      \n'
    firewallForm += '  Back Netmask:      \n\n'
    firewallForm += '  Master Firewall Connection To (Row Agg Sw. ID): '+mfwloc.findsw()+'\n'
    firewallForm += '  Master Firewall Connection Port:                '+mfwloc.findbkport()+'\n\n'
    firewallForm += '  Backup Firewall Connection To (Row Agg Sw. ID): '+sfwloc.findsw()+'\n'
    firewallForm += '  Backup Firewall Connection Port:                '+sfwloc.findbkport()+'\n\n'
    firewallForm += '  SwitchPort Speed/Duplex set to:                 '+speed+'M/Full\n'
    firewallForm += '   (firewalls should be set to the same speed)\n'
    firewallForm += '  INFRA4.0 VLAN (Num/Label):   '+str(backVlan)+'/'+mfwloc.room+'r'+str("%02d" % int(mfwloc.row))+'-'+alLoccode+'-'+backdepth+'\n\n'
    auxIII = 2
    for segment in Segments[2:]:
        firewallForm += '**'+segment+' (Network '+Depths[auxIII]+')\n\n'
        firewallForm += '  Physical Interface: '+nokiaPorts[auxIII]+'\n\n'
        firewallForm += '  Firewall Back-VRRP Interface:    (gateway for ???)\n'
        firewallForm += '  Master Firewall Back Interface: \n'
        firewallForm += '  Backup Firewall Back Interface: \n\n'
        firewallForm += '  Back Netmask:      \n'
        firewallForm += '  Back Network:      \n\n'
        firewallForm += '  Master Firewall Connection To (Row Agg Sw. ID): '+mfwloc.findsw()+'\n'
        firewallForm += '  Master Firewall Connection Port:                gi'+mfwloc.findmod()+'/'+str(Ports[auxIII])+'\n\n'
        firewallForm += '  Backup Firewall Connection To (Row Agg Sw. ID): '+sfwloc.findsw()+'\n'
        firewallForm += '  Backup Firewall Connection Port:                gi'+sfwloc.findmod()+'/'+str(Ports[auxIII])+'\n\n'
        firewallForm += '  SwitchPorts Speed/Duplex set to:                '+speed+'M/Full\n'
        firewallForm += '   (firewalls should be set to the same speed)\n'
        firewallForm += '  INFRA4.0 VLAN (Num/Label):   '+str(Vlans[auxIII])+'/'+mfwloc.room+'r'+str("%02d" % int(mfwloc.row))+'-'+alLoccode+'-'+Depths[auxIII]+'\n\n'
        auxIII += 1
    firewallForm += '**State sync is eth4\n\n'
    print(firewallForm)
    if ips != 'none':
        input('Hit Enter to view the IPS allocation form')
        print()
        # [IF APPLICABLE] IPS allocation form (without IP info)
        ipsform = 'IPS NETWORK INFORMATION:\n'
        ipsform += '--------------------------\n\n'
        ipsform += 'IPS ID: '+ips+'\n'
        ipsform += 'IPS Rack Location: '+ipsloc+'\n\n'
        ipsform += 'IPS Management#1 port\n\n'
        ipsform += '      connection to: '+ipsloc.findsw()+'\n'
        ipsform += '               port: '+ipsloc.findbkport()+' (Green cable)\n'
        ipsform += '          speed/dup: 100M/Full\n'
        ipsform += '   VLAN (Num/Label): '+str(ipsmgtVlan)+'/'+ipsloc.room+'r'+str("%02d" % int(ipsloc.row))+'-'+alLoccode+'-'+ipsmgtDepth+'\n\n'
        if ans1[0] == 'y':
            ipsform += 'IPS inline port 1A\n\n'
            ipsform += '      connection to: '+mfw+'\n'
            ipsform += '               port: '+nokiaPorts[1]+'\n'
            ipsform += '          speed/dup: '+speed+'M/Full\n'
            ipsform += '         cable type: XOVER\n\n'
            ipsform += 'IPS inline port 1B\n\n'
            ipsform += '      connection to: '+ipsloc.findsw()+'\n'
            ipsform += '               port: '+mfwloc.findbkport()+' ('+mfwloc+' green)\n'
            ipsform += '          speed/dup: '+speed+'M/Full\n'
            ipsform += '         cable type: straight-thru \n\n'
            auxIV = 2
            for sniff in Sniff[2:]:
                if sniff == 'y':
                    ipsform += 'IPS inline port 2C\n\n'
                    ipsform += '      connection to: '+mfw+'\n'
                    ipsform += '               port: '+nokiaPorts[auxIV]+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: XOVER\n\n'
                    ipsform += 'IPS inline port 2D\n\n'
                    ipsform += '      connection to: '+ipsloc.findsw()+'\n'
                    ipsform += '               port: gi'+ipsloc.findmod()+'/'+str(Ports[auxIV])+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: straight-thru\n\n'
                    auxIV += 1
                else:
                    auxIV += 1
        else:
            auxV = 0
            auxVI = 2
            for sniff in Sniff[2:]:
                if sniff == 'y':
                    ipsform += 'IPS inline port '+('1A' if auxV == 0 else '2C')+'\n\n'
                    ipsform += '      connection to: '+mfw+'\n'
                    ipsform += '               port: '+nokiaPorts[auxVI]+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: XOVER\n\n'
                    ipsform += 'IPS inline port '+('1B' if auxV == 0 else '2D')+'\n\n'
                    ipsform += '      connection to: '+ipsloc.findsw()+'\n'
                    ipsform += '               port: gi'+ipsloc.findmod()+'/'+str(Ports[auxVI])+'\n'
                    ipsform += '          speed/dup: '+speed+'M/Full\n'
                    ipsform += '         cable type: straight-thru\n\n'
                    auxV += 1
                    auxVI += 1
                else:
                    auxVI += 1
        ipsform += 'IPS Management\n\n'
        ipsform += '       IP: \n'
        ipsform += '  Netmask: \n'
        ipsform += '  Gateway: \n'
        ipsform += 'Broadcast: \n'
        print(ipsform)

if __name__ == '__main__':
    main()
    
