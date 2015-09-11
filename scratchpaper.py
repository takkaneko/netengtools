def devicePorts(sid):
    asa85Ports = ['gi0/0','gi0/1','gi0/2','gi0/3','gi0/4','gi0/5', # for standard network segments or sync
                  'gi1/0','gi1/1','gi1/2','gi1/3','gi1/4','gi1/5', # for standard network segments or sync
                  'gi0/6','gi0/7','gi0/8','gi0/9', # 10G ports for possible sync
                  'gi1/6','gi1/7','gi1/8','gi1/9'] # 10G ports for possible sync
    asa25-50Ports = ['gi0/0','gi0/1','gi0/2','gi0/3','gi0/4','gi0/5','gi0/6','gi0/7'] 
    asa10Ports = ['gi0/0','gi0/1','gi0/2','gi0/3','gi0/4','gi0/5']
    nokia3XXPorts = ['eth1','eth2','eth3','eth4',
                     's1p1','s1p2','s1p3','s1p4',
                     's2p1','s2p2','s2p3','s2p4'] 
    UTM130Ports = ['EXT(5)','INT(1)','LAN1(2)','LAN2(3)','DMZ(4)']
    nokia4400Ports = ['eth1','eth2','eth3','eth4','eth5','eth6','eth7','eth8']
    nokia2200Ports = ['eth1','eth2','eth3','eth4','eth5','eth6']
    alteonPorts = ['p1','p2','p3','p4','p5','p7','p8']
    genericPorts = ['p1','p2','p3','p4','p5','p6','p7','p8','p9','p10']
    if sid.model == 'asa85':
        return asa85Ports
    elif sid.model in ['asa25','asa50']:
        return asa25-50Ports
    elif sid.model == 'asa10':
        return asa10Ports
    elif sid.model == 'alteon':
        return alteonPorts
    elif sid.model == 'chkp13':
        return UTM130Ports
    elif sid.model == 'chkp40':
        return nokia4400Ports
    elif sid.model == 'chkp20':
        return nokia2200Ports
    elif sid.model in ['nokia39','nokia56']:
        return nokia3XXPorts
    else:
        return genericPorts

def defaultsync(sid):
    """
    sid must be an HA-capable device
    """
    if sid.model == 'asa85':
        return 'gi1/5'
    elif sid.model in ['asa25','asa50']:
        return 'gi0/7'
    elif sid.model == 'asa10':
        return 'gi0/5'
    elif sid.model == 'alteon':
        return 'none'
    elif sid.model == 'chkp40':
        return 'eth8'
    elif sid.model == 'chkp20':
        return 'eth6'
    elif sid.model in ['nokia39','nokia56']:
        return 'eth4'
    else:
        return 'p10'

def chooseSyncInt(sid):
    while True:
        try:
            syncinterface = input('Enter a sync interface, or type \'none\' ['+defaultsync(sid)+']: ').lower().strip() or defaultsync(sid)
            if syncinterface in devicePorts(sid):
                break
        except ValueError:
            print('ERROR: INVALID DATA\n')
    return syncinterface

sync = chooseSyncInt(mfw)
devicePorts(sid).remove(syncinterface)







