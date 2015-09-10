def devicePorts(sid):
    asa85Ports = ['gi0/1','gi0/2','gi0/3','gi0/4','gi0/5','gi1/1','gi1/2','gi1/3','gi1/4','gi1/5']
    asa25-50Ports = ['gi0/1','gi0/2','gi0/3','gi0/4','gi0/5','gi0/6','gi0/7'] 
    asa10Ports = ['gi0/1','gi0/2','gi0/3','gi0/4','gi0/5']
    nokiaPorts = ['eth1','eth2','eth3','eth4','s1p1','s1p2','s1p3','s1p4','s2p1','s2p2','s2p3','s2p4'] 
    alteonPorts = ['p1','p2','p3','p4','p5','p7','p8']
    if sid.findmodel() == 'ASA5585':
        return asa85Ports
    elif sid.findmodel() == 'ASA5525' or sid.findmodel() == 'ASA5550':
        return asa25-50Ports
    elif sid.findmodel() == 'ASA5510':
        return asa10Ports
    else:
        return nokiaPorts

def defaultsync(sid):
    if sid.findmodel() == 'ASA5585':
        return 'gi1/5'
    elif sid.findmodel() == 'ASA5525' or sid.findmodel() == 'ASA5550':
        return 'gi0/7'
    elif sid.findmodel() == 'ASA5510':
        return 'gi0/5'
    elif sid.findmodel() == 'Alteon4408':
        return 'none'
    else:
        return 'eth4'

def chooseSyncInt(sid):
    while True:
        try:
            syncinterface = input('Enter a sync interface, or type \'none\' ['+defaultsync(sid)+']: ').lower().strip() or defaultsync(sid)
            break
        except ValueError:
            print('ERROR: INVALID DATA\n')
    return syncinterface
