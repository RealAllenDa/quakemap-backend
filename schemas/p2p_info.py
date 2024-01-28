from enum import Enum
from typing import Literal, Optional

from pydantic import ConfigDict, BaseModel, Field

from schemas.eew import EEWParseReturnModel, EEWCancelledModel
from schemas.geojson import TsunamiGeoJsonModel

# Not really optional, since all the data tagged with this
# would be filled after variable initialization.
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
    source: Optional[str] = None
    time: str
    type: EarthquakeIssueTypeEnum
    correct: Optional[_EarthquakeIssueCorrectEnum] = None


# --- Earthquake - Epicenter
class EarthquakeEpicenterModel(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    depth: Optional[int] = None
    magnitude: Optional[float] = None


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
    hypocenter: Optional[EarthquakeEpicenterModel] = None
    max_scale: Optional[EarthquakeScaleEnum] = Field(None, validation_alias="maxScale")
    domestic_tsunami: Optional[EarthquakeDomesticTsunamiEnum] = Field(None, validation_alias="domesticTsunami")
    foreign_tsunami: Optional[EarthquakeForeignTsunamiEnum] = Field(None, validation_alias="foreignTsunami")
    model_config = ConfigDict(populate_by_name=True)


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
    prefecture: str = Field(validation_alias="pref")
    address: str = Field(validation_alias="addr")
    is_area: bool = Field(validation_alias="isArea")
    scale: EarthquakePointsScaleEnum
    model_config = ConfigDict(populate_by_name=True)


# --- Earthquake - Export
class P2PQuakeModel(_BasicDataModel):
    code: Literal[551]
    issue: _EarthquakeIssueModel
    earthquake: _EarthquakeModel
    points: Optional[list[_EarthquakePoints]] = None


# --- Tsunami - Area
class TsunamiAreaGradeEnum(str, Enum):
    MajorWarning = "MajorWarning"
    Warning = "Warning"
    Watch = "Watch"
    Unknown = "Unknown"


class TsunamiAreaModel(BaseModel):
    grade: Optional[TsunamiAreaGradeEnum] = None
    immediate: Optional[bool] = None
    name: Optional[str] = None


# --- Tsunami - Issue
class _TsunamiIssueModel(BaseModel):
    source: str
    time: str
    type: str


# --- Tsunami - Export
class P2PTsunamiModel(_BasicDataModel):
    code: Literal[552]
    cancelled: bool
    issue: _TsunamiIssueModel
    areas: Optional[list[TsunamiAreaModel]] = None


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
    is_area: Literal[True] = True
    intensity_code: EarthquakePointsScaleEnum


class EarthquakeStationIntensityPointModel(EarthquakeAreaIntensityPointModel):
    is_area: Literal[False] = False
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
    time: Optional[str] = None
    areas: Optional[TsunamiGeoJsonModel] = None


class P2PTotalInfoModel(BaseModel):
    earthquake: list[EarthquakeReturnModel] = []
    tsunami: Optional[TsunamiReturnModel] = None
    tsunami_in_effect: str = "0"


class EarthquakeInfoReturnModel(BaseModel):
    info: list[EarthquakeReturnModel]
    eew: dict | EEWParseReturnModel | EEWCancelledModel
