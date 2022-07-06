from enum import Enum

__all__ = ["ModulesEnum", "ModulesClassEnum"]


class ModulesEnum(str, Enum):
    eew = "eew_info"
    tsunami = "tsunami"
    p2p_earthquake = "p2p_info"
    shake_level = "shake_level"
    global_earthquake = "global_earthquake"


class ModulesClassEnum(str, Enum):
    eew = "EEWInfo"
    tsunami = "TsunamiInfo"
    p2p_earthquake = "P2PInfo"
    shake_level = "ShakeLevel"
    global_earthquake = "GlobalEarthquake"
