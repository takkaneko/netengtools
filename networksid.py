#!/usr/bin/env python3
# networksid.py

import re

# HA FW/LB SIDs:

# netsvc20043
# nokia39hamfw10093
# alteonhamslb10317
# nokia56hamfw20002
# asa10hamfw16000
# asa25hamfw20003
# asa50hamfw20001
# asa50hamfw10001
# pixhamfw10027

# Stand-alone FW/LB SIDs:

# nokia39fw20018
# nokia39fw10004
# nokia29fw10030
# chkp13fw10093
# chkp20fw10001
# alteonslb10332
# fw20002
# asa10fw10001
# pixfw16006

# IPS SIDs:

# prgx4aips10011
# prgx5aips20001
# prvg100aips10007

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
        p1 = re.compile(r"^(nokia39|nokia56|alteon|asa10|asa25|asa50|pix)+(ham|has)+(fw|slb)+(\d{5})$", re.IGNORECASE) # HA master/standby fw/lb
        p2 = re.compile(r"^(netsvc)+(\d{5})$", re.IGNORECASE) # Generic network device
        p3 = re.compile(r"^(nokia39|nokia56|nokia29|chkp13|chkp20|alteon|asa10|pix)+(fw|slb)+(\d{5})$", re.IGNORECASE) # Stand-alone fw/lb
        p4 = re.compile(r"^(fw)+(\d{5})$", re.IGNORECASE) # Unknown model firewall (Not common)
        p5 = re.compile(r"^(prgx4|prgx5|prvg100)+(aips)+(\d{5})$", re.IGNORECASE) # IPS
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
            self.model = 'unknown'
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
        else:
            model = p5.match(sid).group(1)
            self.model = model
            self.role = 'stand-alone'
            self.type = 'ips'
            digits = p5.match(sid).group(3)
            self.digits = digits

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

    def is_ips(self):
        """
        Boolean that determines if the service id represents an ips or not.
        """
        return True if re.search('ips',self.type) else False

    def peersid(self):
        """
        Returns an HA peer's service ID.
        """
        if self.role == 'ham':
            peer = self.model + 'has' + self.type + self.digits
        elif self.role == 'has':
            peer = self.model + 'ham' + self.type + self.digits
        peer = NWdevice(peer)
        return peer
    

