from enum import Enum
from typing import Dict

class Connector(Enum):
    CHANGING = 'CHANGING'
    NOT_CONNECTED = 'NOT_CONNECTED'
    CONNECTED = 'CONNECTED'
    SEARCH_COMM = 'SEARCH_COMM'
    RCD_FAULT = 'RCD_FAULT'
    CHARGING = 'CHARGING'
    CHARGING_PAUSED = 'CHARGING_PAUSED'
    CHARGING_FINISHED = 'CHARGING_FINISHED'
    CHARGING_CANCELLED = 'CHARGING_CANCELLED'
    DISABLED = 'DISABLED'
    OVERHEAT = 'OVERHEAT'
    CRITICAL_TEMPERATURE = 'CRITICAL_TEMPERATURE'
    INITIALIZATION = 'INITIALIZATION'
    CABLE_FAULT = 'CABLE_FAULT'
    LOCK_FAULT = 'LOCK_FAULT'
    CONTACTOR_FAULT = 'CONTACTOR_FAULT'
    VENT_FAULT = 'VENT_FAULT'
    DC_ERROR = 'DC_ERROR'
    DC_HARDWARE = 'DC_HARDWARE'
    CP_FAULT = 'CP_FAULT'
    CP_SHORTED = 'CP_SHORTED'
    REMOTE_DISABLED = 'REMOTE_DISABLED'
    UNKNOWN = 'UNKNOWN'
    UNAVAILABLE = 'UNAVAILABLE'

class Mode(Enum):
    ON = 'ALWAYS_ON'
    OFF = 'ALWAYS_OFF'
    SCHEMA = 'SCHEMA'

class PowerMode(Enum):
    ON = 'ON'
    OFF  = 'OFF'
    UNKNOWN = 'UNKNOWN'
    UNAVAILABLE = 'UNAVAILABLE'

class CableLockMode(Enum):
    UNLOCKED = 0
    LOCKED = 2
    LOCKED_WITH_POWER_LOSS_UNLOCK = 1

class GaroProductInfo:
    def __init__(self, name: str, has_meter: bool = False, is_3_phase: bool = False, has_outlet: bool = False):
        self.name = name
        self.has_meter = has_meter
        self.is_3_phase = is_3_phase
        self.has_outlet = has_outlet


PRODUCT_MAP: Dict[int, GaroProductInfo] = {
    1: GaroProductInfo('GLBMW-T137FC', True, False, False ),
    2: GaroProductInfo('GLBMW-T237FC', True, False, False ),
    3: GaroProductInfo('GLBMW-T237WO', True, False, True ),
    4: GaroProductInfo('GLBW-T174FC-B', False, False, False ),
    5: GaroProductInfo('GLBW-T274FC-B', False, False, False ),
    6: GaroProductInfo('GLBMW-T274WO', True, False, True ),
    7: GaroProductInfo('GLBW-T137FC', False, False, False ),
    8: GaroProductInfo('GLBW-T237FC', False, False, False ),
    9: GaroProductInfo('GLBW-T237WO', False, False, True ),
    10: GaroProductInfo('GLBW-T174FC', False, False, False ),
    11: GaroProductInfo('GLBW-T274FC', False, False, False ),
    12: GaroProductInfo('GLBM-T274WO', True, False, True ),
    13: GaroProductInfo('GLBW-T222FC', False, True, False ),
    14: GaroProductInfo('GLBW-T222FC-B', False, True, False ),
    15: GaroProductInfo('GLBW-T222WO', False, True, True ),
    16: GaroProductInfo('GLBW-T222WO-B', False, True, True ),
    17: GaroProductInfo('GLB-T137FC', False, False, False ),
    18: GaroProductInfo('GLB-T237FC', False, False, False ),
    19: GaroProductInfo('GLB-T237WO', False, False, True ),
    20: GaroProductInfo('GLB-T174FC', False, False, False ),
    21: GaroProductInfo('GLB-T274FC', False, False, False ),
    22: GaroProductInfo('GLBM-T274WO-B', True, False, True ),
    23: GaroProductInfo('GLB-T222FC', False, True, False ),
    24: GaroProductInfo('GLB-T222FC-B', False, True, False ),
    25: GaroProductInfo('GLB-T222WO', False, True, True ),
    26: GaroProductInfo('GLB-T222WO-B', False, True, True ),
    27: GaroProductInfo('GLBMW-T274WO-B', True, False, True ),
    28: GaroProductInfo('GLB-T174FC-B', False, False, False ),
    29: GaroProductInfo('GLB-T274FC-B', False, False, False ),
    30: GaroProductInfo('GLBM-T237WO', True, False, True ),
    31: GaroProductInfo('GLBM-T137FC', True, False, False ),
    32: GaroProductInfo('GLBM-T237FC', True, False, False ),
    33: GaroProductInfo('GLBMMFF-T237WO', True, False, True ),
    34: GaroProductInfo('GLBMMFF-T274WO-B', True, False, True ),
    35: GaroProductInfo('GLBMMFF-T274WO', True, False, True ),
    36: GaroProductInfo('GLBMN-T222WO-B', False, True, True ),
    37: GaroProductInfo('GLB-MN-T222WO', True, True, True ),
    38: GaroProductInfo('GLBMMN-T222WO', True, True, True ),
    39: GaroProductInfo('GLBMB-T237WO', False, False, True ),
    40: GaroProductInfo('GLBMFF-T237WO-B', True, False, True ),
    41: GaroProductInfo('GLBMMFF-T237WO-B', True, False, True ),
    42: GaroProductInfo('GHL-T274WOI', False, False, True ),
    43: GaroProductInfo('GLBP-T237WO', False, False, True ),
    44: GaroProductInfo('GLBP-T137FC', False, False, False ),
    45: GaroProductInfo('GLBP-T222WO-B', False, False, True ),
    46: GaroProductInfo('GLBP-T222WO', False, True, True ),
    47: GaroProductInfo('GLBP-T222FC-B', False, True, False ),
    48: GaroProductInfo('GLBP-T222FC', False, True, False ),
    49: GaroProductInfo('GLBPW-T237WO', False, False, True ),
    50: GaroProductInfo('GLBPW-T137FC', False, False, False ),
    51: GaroProductInfo('GLBPW-T222WO-B', False, True, True ),
    52: GaroProductInfo('GLBPW-T222WO', False, True, True ),
    53: GaroProductInfo('GLBPW-T222FC-B', False, True, False ),
    54: GaroProductInfo('GLBPW-T222FC', False, True, False ),
    55: GaroProductInfo('GLBPMN-T222WO', True, True, True ),
    56: GaroProductInfo('GLBPMMN-T222WO', True, True, True ),
    57: GaroProductInfo('GLBDC-T137FC-A', False, False, False ),
    58: GaroProductInfo('GLBDC-T237FC-A', False, False, False ),
    59: GaroProductInfo('GLBDC-T274WO-A', False, False, True ),
    60: GaroProductInfo('GLBDCM-T137FC-A', True, False, False ),
    61: GaroProductInfo('GLBDCM-T237FC-A', True, False, False ),
    62: GaroProductInfo('GLBDCM-T274WO-A', True, False, True ),
    63: GaroProductInfo('GLBDCM-T274FC-A', True, False, False ),
    64: GaroProductInfo('GLBDC-T222FC-A', False, True, False ),
    65: GaroProductInfo('GLBDCM-T222FC', False, True, False ),
    66: GaroProductInfo('GLBDC-T222WO-A', False, True, True ),
    67: GaroProductInfo('GLBDCM-T222WO', False, True, True ),
    68: GaroProductInfo('GLBDC-T174FC', False, False, False ),
    69: GaroProductInfo('GLBDCM-T274WO', True, False, True ),
    70: GaroProductInfo('GLBDC-T222WO', False, True, True ),
    71: GaroProductInfo('GLBDC-T222FC', False, True, False ),
    72: GaroProductInfo('GLBDCMB-T274WO-A', True, False, True ),
    73: GaroProductInfo('GLBDCM-T274WO-A-NO', True, False, True ),
    74: GaroProductInfo('GLBDC-T174FC-A', False, False, False ),
    75: GaroProductInfo('GLBDC-T274FC', False, False, False ),
    76: GaroProductInfo('GLBPDC-T222FC-A', False, True, False ),
    77: GaroProductInfo('GLBPDCM-T222FC', True, True, False ),
    78: GaroProductInfo('GLBPDC-T222WO-A', False, True, True ),
    79: GaroProductInfo('GLBPDCM-T222WO', True, True, True ),
    80: GaroProductInfo('GLBPDC-T222WO', False, True, True ),
    81: GaroProductInfo('GLBPDC-T222FC', False, True, False ),
    82: GaroProductInfo('GLBDCM-T274FC', True, False, False ),
    83: GaroProductInfo('GLBDCW-T274FC-A VO', False, False, False ),
    84: GaroProductInfo('GLBDCWM-T137FC-A', False, False, False ),
    85: GaroProductInfo('GLBDCWM-T237FC-A', False, False, False ),
    86: GaroProductInfo('GLBDCWM-T274WO-A', False, False, True ),
    87: GaroProductInfo('GLBDCWM-T222FC', False, True, False ),
    88: GaroProductInfo('GLBDCWM-T222WO', False, True, True ),
    89: GaroProductInfo('GLBDCWM-T274FC-A', False, False, False ),
    90: GaroProductInfo('GLBDCW-T211FC', False, True, False ),
    91: GaroProductInfo('GLBDCW-T222FC', False, True, False ),
    92: GaroProductInfo('GTCDC-T274WO-A', False, False, True ),
    93: GaroProductInfo('GTCDCMW-T274WO-A', True, False, True ),
    94: GaroProductInfo('GTBDCM-T222WO-A', True, True, True ),
    95: GaroProductInfo('GTBDCM-T211FC-A', True, True, False ),
    96: GaroProductInfo('GTBDCM-T211FC-A', True, False, True ),
    97: GaroProductInfo('GTBDCM-T274FC-A', True, False, False ),
    98: GaroProductInfo('GTBDCMB-T274WO-A', False, False, True ),
    99: GaroProductInfo('GTBDCMB-T222WO-A', False, True, True ),
    100: GaroProductInfo('GTBDC-T222WO-A', False, True, True ),
    101: GaroProductInfo('GTBDC-T274WO-A', False, False, True ),
    102: GaroProductInfo('GTBDC-T274FC-A', False, False, False ),
    103: GaroProductInfo('GTBDCMW-T274WO-A', True, False, True ),
    104: GaroProductInfo('GTBDCMW-T222WO-A', True, True, True ),
    105: GaroProductInfo('GTBDCMW-T274FC-A', True, False, False ),
    106: GaroProductInfo('GTBDCMW-T211FC-A', True, True, False ),
    107: GaroProductInfo('GLBDCM-T222WO', False, True, True ),
    108: GaroProductInfo('GLBDCM-T274WO-A', True, False, True ),
    109: GaroProductInfo('GLBDCM-T222FK', True, True, False ),
    110: GaroProductInfo('GLBDCM-T222WO', True, True, True ),
    111: GaroProductInfo('GLBDCM-T274FK-A', True, False, False ),
    112: GaroProductInfo('GLBDCWM-T222FC8', True, True, False ),
    113: GaroProductInfo('GLBDCW-T222WOF-VCC', False, True, True ),
    114: GaroProductInfo('GLBDC-T274WO PME', False, True, True ),
    115: GaroProductInfo('GLBDC-T274FC PME', False, True, False ),
    116: GaroProductInfo('GTBDCMW-T222FC-A', True, True, False ),
    117: GaroProductInfo('GTBDCMW-T211FCL-A', True, True, False ),
    118: GaroProductInfo('GTBDCW-T211FCL-A', False, True, False ),
    119: GaroProductInfo('GLBDCMW-T211FC-VCC', True, True, False ),
    120: GaroProductInfo('GLBDCMW-T222FC-VCC', True, True, False ),
    121: GaroProductInfo('GLBDCW-T222FC-A-VCC', False, True, False ),
    122: GaroProductInfo('GLBDCWM-T222WO-VCC', True, True, True ),
    220: GaroProductInfo('CLS1-DCM-W-T223WO-A', False, True, False ),
    221: GaroProductInfo('CLS1-DCM-W-T237WO-A', False, True, False )
}