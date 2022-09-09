from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

__all__ = ["EarthquakeInfoReturnModel",

           "P2PQuakeModel", "P2PTsunamiModel", "P2PTotalInfoModel",
           "EarthquakeIntensityEnum", "EarthquakeTsunamiCommentsModel",
           "EarthquakeReturnModel", "EarthquakeAreaIntensityModel",

           "EarthquakeIssueTypeEnum", "EarthquakeScaleEnum", "EarthquakePointsScaleEnum",
           "EarthquakeReturnEpicenterModel",
           "EarthquakeDomesticTsunamiEnum", "EarthquakeForeignTsunamiEnum",

           "EarthquakeAreaIntensityParsingModel", "EarthquakeAreaIntensityPointModel",
           "EarthquakeStationIntensityPointModel",

           "TsunamiAreaGradeEnum", "TsunamiAreaModel", "TsunamiReturnModel"]

# Not really optional, since all the data tagged with this
# would be filled after variable initialization.
from model.eew import EEWParseReturnModel
from model.geojson import TsunamiGeoJsonModel

FakeOptional = Optional
# The dict which shall always be blank.
BlankDict = dict


# --- Basic Data
class _BasicDataModel(BaseModel):
    id: str
    time: str
    code: int


# --- Earthquake - Issue
class EarthquakeIssueTypeEnum(str, Enum):
    ScalePrompt = "ScalePrompt"
    Destination = "Destination"
    ScaleAndDestination = "ScaleAndDestination"
    DetailScale = "DetailScale"
    Foreign = "Foreign"
    Other = "Other"


class _EarthquakeIssueCorrectEnum(str, Enum):
    No = "None"
    Unknown = "Unknown"
    ScaleOnly = "ScaleOnly"
    DestinationOnly = "DestinationOnly"
    ScaleAndDestination = "ScaleAndDestination"


class _EarthquakeIssueModel(BaseModel):
    source: Optional[str]
    time: str
    type: EarthquakeIssueTypeEnum
    correct: Optional[_EarthquakeIssueCorrectEnum]


# --- Earthquake - Epicenter
class EarthquakeEpicenterModel(BaseModel):
    name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    depth: Optional[int]
    magnitude: Optional[float]


class EarthquakeScaleEnum(int, Enum):
    no = -1
    one = 10
    two = 20
    three = 30
    four = 40
    five_lower = 45
    five_upper = 50
    six_lower = 55
    six_upper = 60
    seven = 70


class EarthquakeDomesticTsunamiEnum(str, Enum):
    No = "None"
    Unknown = "Unknown"
    Checking = "Checking"
    NonEffective = "NonEffective"
    Watch = "Watch"
    Warning = "Warning"


class EarthquakeForeignTsunamiEnum(str, Enum):
    No = "None",
    Unknown = "Unknown",
    Checking = "Checking",
    NonEffectiveNearby = "NonEffectiveNearby",
    WarningNearby = "WarningNearby",
    WarningPacific = "WarningPacific",
    WarningPacificWide = "WarningPacificWide",
    WarningIndian = "WarningIndian",
    WarningIndianWide = "WarningIndianWide",
    Potential = "Potential"


# --- Earthquake - Content
class _EarthquakeModel(BaseModel):
    time: str
    hypocenter: Optional[EarthquakeEpicenterModel]
    max_scale: Optional[EarthquakeScaleEnum]
    domestic_tsunami: Optional[EarthquakeDomesticTsunamiEnum]
    foreign_tsunami: Optional[EarthquakeForeignTsunamiEnum]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "time": "time",
            "hypocenter": "hypocenter",
            "max_scale": "maxScale",
            "domestic_tsunami": "domesticTsunami",
            "foreign_tsunami": "foreignTsunami"
        }


# --- Earthquake - Points
class EarthquakePointsScaleEnum(int, Enum):
    one = 10
    two = 20
    three = 30
    four = 40
    five_lower = 45
    bigger_than_five_lower = 46
    five_upper = 50
    six_lower = 55
    six_upper = 60
    seven = 70


class _EarthquakePoints(BaseModel):
    prefecture: str
    address: str
    is_area: bool
    scale: EarthquakePointsScaleEnum

    class Config:
        allow_population_by_field_name = True
        fields = {
            "prefecture": "pref",
            "address": "addr",
            "is_area": "isArea",
            "scale": "scale"
        }


# --- Earthquake - Export
class P2PQuakeModel(_BasicDataModel):
    code = Field(551, const=True)
    issue: _EarthquakeIssueModel
    earthquake: _EarthquakeModel
    points: Optional[list[_EarthquakePoints]]


# --- Tsunami - Area
class TsunamiAreaGradeEnum(str, Enum):
    MajorWarning = "MajorWarning"
    Warning = "Warning"
    Watch = "Watch"
    Unknown = "Unknown"


class TsunamiAreaModel(BaseModel):
    grade: Optional[TsunamiAreaGradeEnum]
    immediate: Optional[bool]
    name: Optional[str]


# --- Tsunami - Issue
class _TsunamiIssueModel(BaseModel):
    source: str
    time: str
    type: str


# --- Tsunami - Export
class P2PTsunamiModel(_BasicDataModel):
    code = Field(552, const=True)
    cancelled: bool
    issue: _TsunamiIssueModel
    areas: Optional[list[TsunamiAreaModel]]


# ========== Internal Parsing
class EarthquakeIntensityEnum(str, Enum):
    no = "-1"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five_lower = "5-"
    five_upper = "5+"
    bigger_than_five_lower = "5?"
    six_lower = "6-"
    six_upper = "6+"
    seven = "7"


class EarthquakeAreaIntensityPointModel(BaseModel):
    name: str
    intensity: EarthquakeIntensityEnum
    latitude: str
    longitude: str
    is_area: bool = Field(True, const=True)
    intensity_code: EarthquakePointsScaleEnum


class EarthquakeStationIntensityPointModel(EarthquakeAreaIntensityPointModel):
    is_area: bool = Field(False, const=True)
    region_code: str
    region_name: str


class EarthquakeAreaIntensityModel(BaseModel):
    areas: dict[str, EarthquakeAreaIntensityPointModel]
    station: dict[str, EarthquakeStationIntensityPointModel]


class EarthquakeAreaIntensityParsingModel(BaseModel):
    content: dict[str, EarthquakeAreaIntensityPointModel | EarthquakeStationIntensityPointModel] = {}


# ========== API Return Model

class EarthquakeTsunamiCommentsModel(BaseModel):
    domestic: FakeOptional[EarthquakeDomesticTsunamiEnum]
    foreign: FakeOptional[EarthquakeForeignTsunamiEnum]


class EarthquakeReturnEpicenterModel(BaseModel):
    name: str
    latitude: float
    longitude: float
    depth: str


class EarthquakeReturnModel(BaseModel):
    type: EarthquakeIssueTypeEnum
    occur_time: str
    receive_time: str
    magnitude: str
    max_intensity: EarthquakeIntensityEnum
    tsunami_comments: EarthquakeTsunamiCommentsModel
    hypocenter: EarthquakeReturnEpicenterModel | BlankDict
    area_intensity: EarthquakeAreaIntensityModel | BlankDict


class TsunamiReturnModel(BaseModel):
    time: Optional[str]
    areas: Optional[TsunamiGeoJsonModel]


class P2PTotalInfoModel(BaseModel):
    earthquake: list[EarthquakeReturnModel] = []
    tsunami: Optional[TsunamiReturnModel]
    tsunami_in_effect: str = "0"


class EarthquakeInfoReturnModel(BaseModel):
    info: list[EarthquakeReturnModel]
    eew: dict | EEWParseReturnModel
