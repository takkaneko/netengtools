NX_OS_IAD = (
    'iad-nex930001',
    'iad-nex930002',
    'iad-nex930003',
    'iad-nex930004',
    'iad-nex930005',
    'iad-nex930006',
    'iad-nex930007',
    'iad-nex930008',
    'iad-nex930009',
    'iad-nex930010',
    'iad-nex930011',
#   'iad-nex93test',    DECOMM'D
)

ASA_IAD = (
    'iad-asa550001',
    'iad-asa550002',
    'iad-asa550003',
    'iad-asa550004',
    'iad-asa550005',
    'iad-asa550006',
    'iad-asa550007',
    'iad-asa550008',
    'iad-asa550009',
    'iad-asa550010',
    'iad-asa550011',
#   'iad-asa55test',    DECOMM'D
)

IOS_IAD = (
    'iad-cat350001',
    'iad-cat350002',
    'iad-cat350003',
    'iad-cat350004',
    'iad-cat350005',
)

IOS_XE_IAD = (
    'iad-asr100001',
    'iad-asr100002',
    'iad-asr100003',
    'iad-asr100004',
    'iad-asr100005',
    'iad-asr100006',
    'iad-asr100007',
    'iad-asr100008',
    'iad-asr100009',
    'iad-asr100010',
    'iad-asr100011',
#   'iad-asr10test',
)

IOS_XR_IAD = (
    'iad-asr900001',
    'iad-asr900002',
)

ALL_NW_DEVICES_IAD = NX_OS_IAD + ASA_IAD + IOS_IAD + IOS_XE_IAD + IOS_XR_IAD

NX_OS_SJC = (
    'sjc-nex930001',
    'sjc-nex930002',
    'sjc-nex930003',
    'sjc-nex930004',
    'sjc-nex930005',
    'sjc-nex930006',
    'sjc-nex930007',
    'sjc-nex930008',
    'sjc-nex930009',
    'sjc-nex930010',
    'sjc-nex930011',
#   'sjc-nex93test',    DECOMM'D
)

ASA_SJC = (
    'sjc-asa550001',
    'sjc-asa550002',
    'sjc-asa550003',
    'sjc-asa550004',
    'sjc-asa550005',
    'sjc-asa550006',
    'sjc-asa550007',
    'sjc-asa550008',
    'sjc-asa550009',
    'sjc-asa550010',
    'sjc-asa550011',
#   'sjc-asa55test',    DECOMM'D
)

IOS_SJC = (
    'sjc-cat350001',
    'sjc-cat350002',
    'sjc-cat350003',
    'sjc-cat350004',
    'sjc-cat350005',
)

IOS_XE_SJC = (
    'sjc-asr100001',
    'sjc-asr100002',
    'sjc-asr100003',
    'sjc-asr100004',
    'sjc-asr100005',
    'sjc-asr100006',
    'sjc-asr100007',
    'sjc-asr100008',
    'sjc-asr100009',
    'sjc-asr100010',
    'sjc-asr100011',
#   'sjc-asr10test',
)

IOS_XR_SJC = (
    'sjc-asr900001',
    'sjc-asr900002',
)
    
ALL_NW_DEVICES_SJC = NX_OS_SJC + ASA_SJC + IOS_SJC + IOS_XE_SJC + IOS_XR_SJC

ALL_NW_DEVICES = ALL_NW_DEVICES_IAD + ALL_NW_DEVICES_SJC

NX_OS = NX_OS_IAD + NX_OS_SJC
ASA = ASA_IAD + ASA_SJC
IOS = IOS_IAD + IOS_SJC
IOS_XE = IOS_XE_IAD + IOS_XE_SJC
IOS_XR = IOS_XR_IAD + IOS_XR_SJC

MONOCONTEXT_ASA = (
    'iad-asa550001',
    'iad-asa550002',
    'iad-asa550003',
    'iad-asa550004',
    'iad-asa550005',
    'sjc-asa550001',
    'sjc-asa550002',
    'sjc-asa550003',
    'sjc-asa550004',
    'sjc-asa550005',
)

MULTICONTEXT_ASA = (
    'iad-asa550006',
    'iad-asa550007',
    'iad-asa550008',
    'iad-asa550009',
    'iad-asa550010',
    'iad-asa550011',
    'sjc-asa550006',
    'sjc-asa550007',
    'sjc-asa550008',
    'sjc-asa550009',
    'sjc-asa550010',
    'sjc-asa550011',
)
