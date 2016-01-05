#!/usr/bin/env python3
# networksid.py

import re

# EXAMPLES - HA FW/LB SIDs:

# netsvc20043 - two different 'netsvcXXXXX' devices *could* form an HA pair
# netsvcham10060
# chkp20hamfw12345
# chkp40hamfw12345
# chkp120hamfw12345
# nokia39hamfw10093
# alteonhamslb10317
# nokia56hamfw20002
# asa10hamfw16000
# asa25hamfw20003
# asa50hamfw20001
# asa85hamfw10001
# pixhamfw10027 - unsupported

# EXAMPLES - Stand-alone FW/LB SIDs:

# nokia39fw20018
# nokia39fw10004
# nokia29fw10030
# chkp13fw10093
# chkp20fw10001
# chkp40fw10101
# alteonslb10332
# fw20002
# asa10fw10001
# pixfw16006

# EXAMPLES - IPS SIDs:

# prgx4aips10011
# prgx5aips20001
# prvg100aips10007

#####NOTE#####
# Every time it becomes necessary to support a new platform (and therefore a new service ID prefix),
# be sure to update the definition of the NWdevice class as well as the following functions in resources.py:

# devicePorts
# defaultsync

##############

class NWdevice(str):
    """
    Service ID format of common network devices. Useful for data validations.
    
    example:
    sid = NWdevice('nokia39hamfw10093')
    
    >>> sid.is_master()
    True
    >>> sid.is_secondary()
    False
    >>> sid.is_fw()
    True
    >>> sid.is_lb()
    False
    """
    def __init__(self,sid):
        p1 = re.compile(r"^(nokia39|nokia56|chkp40|chkp20|chkp120|alteon|asa10|asa25|asa50|asa85)+(ham|has)+(fw|slb)+(\d{5})$", re.IGNORECASE) # HA master/standby fw/lb
        p2 = re.compile(r"^(netsvc)+(\d{5})$", re.IGNORECASE) # Generic HA or non-HA network device
        p3 = re.compile(r"^(nokia39|nokia56|nokia29|chkp13|chkp20|chkp40|chkp120|alteon|asa10)+(fw|slb)+(\d{5})$", re.IGNORECASE) # Stand-alone fw/lb
        p4 = re.compile(r"^(fw)+(\d{5})$", re.IGNORECASE) # Unknown model firewall (Not common)
        p5 = re.compile(r"^(prgx4|prgx5|prvg100)+(aips)+(\d{5})$", re.IGNORECASE) # IPS
        p6 = re.compile(r"^(netsvc)+(ham|has)+(\d{5})$", re.IGNORECASE) # Generic HA master/secondary network device
        if p1.match(sid):
            model = p1.match(sid).group(1)
            self.model = model
            role = p1.match(sid).group(2)
            self.role = role
            type = p1.match(sid).group(3)
            self.type = type
            digits = p1.match(sid).group(4)
            self.digits = digits
        elif p2.match(sid):
            model = p2.match(sid).group(1)
            self.model = model
            self.role = 'ham or has or stand-alone'
            self.type = 'fw or slb'
            self.digits = p2.match(sid).group(2)
        elif p3.match(sid):
            model = p3.match(sid).group(1)
            self.model = model
            self.role = 'stand-alone'
            type = p3.match(sid).group(2)
            self.type = type
            digits = p3.match(sid).group(3)
            self.digits = digits
        elif p4.match(sid):
            self.model = 'unknown'
            self.role = 'stand-alone'
            self.type = 'fw'
            self.digits = p4.match(sid).group(2)
        elif p5.match(sid):
            model = p5.match(sid).group(1)
            self.model = model
            self.role = 'stand-alone'
            self.type = 'ips'
            digits = p5.match(sid).group(3)
            self.digits = digits
        else:
            model = p6.match(sid).group(1)
            self.model = model
            role = p6.match(sid).group(2)
            self.role = role
            self.type = 'fw or slb'
            digits = p6.match(sid).group(3)
            self.digits = digits

    def findVendor(self):
        """
        Returns 'cisco' or 'nokia'
        """
        if self.model in ['nokia39','nokia56','chkp40','chkp20','chkp120','chkp13']:
            return 'nokia'
        elif self.model in ['asa10','asa25','asa50','asa85']:
            return 'cisco'
    
    def is_master(self):
        """
        Boolean that determines if the service id represents a master device or not.
        """
        return True if re.search('ham',self.role) else False 

    def is_secondary(self):
        """
        Boolean that determines if the service id represents a standby device or not.
        """
        return True if re.search('has',self.role) else False

    def is_solo(self):
        """
        Boolean that determines if the service id represents a stand-alone device or not.
        """
        return True if re.search('stand-alone',self.role) else False
        
    
    def is_fw(self):
        """
        Boolean that determines if the service id represents a firewall or not.
        """
        return True if re.search('fw',self.type) else False
    
    def is_lb(self):
        """
        Boolean that determines if the service id represents a loadbalancer or not.
        """
        return True if re.search('slb',self.type) else False

    def is_fw_or_lb(self,devicetype):
        """
        Combining is_fw() and is_lb(). devicetype must be either 'firewall' or 'loadbalancer.'
        """
        if devicetype == 'firewall':
            return True if re.search('fw',self.type) else False
        else:
            return True if re.search('slb',self.type) else False

    def is_ips(self):
        """
        Boolean that determines if the service id represents an ips or not.
        """
        return True if re.search('ips',self.type) else False

    def peersid(self):
        """
        Returns an HA peer's service ID.
        """
        if re.match(r"^(nokia39|nokia56|chkp40|chkp20|chkp120|alteon|asa10|asa25|asa50|asa85)+(ham|has)+(fw|slb)+(\d{5})$",self):
            if self.role == 'ham':
                peer = self.model + 'has' + self.type + self.digits
            elif self.role == 'has':
                peer = self.model + 'ham' + self.type + self.digits
            peer = NWdevice(peer)
        else:
            if self.role == 'ham':
                peer = self.model + 'has' + self.digits
            elif self.role == 'has':
                peer = self.model + 'ham' + self.digits
            peer = NWdevice(peer)
        return peer
    
    def site(self):
        """
        'sjc' or 'iad'
        """
        return 'iad' if self.digits[0] == '1' else 'sjc'


