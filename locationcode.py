#!/usr/bin/env python3
# locationcode.py

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


