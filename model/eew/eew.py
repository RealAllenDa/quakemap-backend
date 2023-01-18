from enum import Enum
from typing import Optional

from pydantic import BaseModel

__all__ = ["KmoniTimeModel", "KmoniEEWModel", "EEWReturnModel",
           "EEWAlertTypeEnum", "EEWConvertedIntensityEnum", "EEWIntensityEnum",
           "EEWParseReturnModel", "KmoniReturnHypocenterModel", "KmoniReturnAreaColoringModel",
           "EEWCancelledModel"]

from model.intensity2color import StationIntensityModel, AreaIntensityModel

OnlyBlankStr = str


# --- Utility Models
class _KmoniResultModel(BaseModel):
    status: str
    message: str


class _KmoniSecurityModel(BaseModel):
    realm: str
    hash: str


class _KmoniEEWResultModel(_KmoniResultModel):
    is_auth: bool


# --- Kmoni: Time
class KmoniTimeModel(BaseModel):
    security: _KmoniSecurityModel
    latest_time: str
    request_time: str
    result: _KmoniResultModel


# --- Kmoni: EEW
class EEWAlertTypeEnum(str, Enum):
    forecast = 0
    warning = 1
    default = 2


class EEWIntensityEnum(str, Enum):
    blank = ""
    no = "0"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five_lower = "5弱"
    five_upper = "5強"
    six_lower = "6弱"
    six_upper = "6強"
    seven = "7"


class EEWConvertedIntensityEnum(str, Enum):
    blank = "0"
    no = "0"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five_lower = "5-"
    five_upper = "5+"
    six_lower = "6-"
    six_upper = "6+"
    seven = "7"


class KmoniEEWModel(BaseModel):
    result: _KmoniEEWResultModel
    report_time: str
    region_code: str
    request_time: str
    region_name: str
    longitude: str
    is_cancel: bool | OnlyBlankStr
    depth: str
    calculated_intensity: EEWIntensityEnum
    is_final: bool | OnlyBlankStr
    is_training: bool | OnlyBlankStr
    latitude: str
    origin_time: str
    security: _KmoniSecurityModel
    magnitude: str
    report_number: int | OnlyBlankStr
    request_hypocenter_type: str
    report_id: str
    alert_flag: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "result": "result",
            "report_time": "report_time",
            "region_code": "region_code",
            "request_time": "request_time",
            "region_name": "region_name",
            "longitude": "longitude",
            "is_cancel": "is_cancel",
            "depth": "depth",
            "calculated_intensity": "calcintensity",
            "is_final": "is_final",
            "is_training": "is_training",
            "latitude": "latitude",
            "origin_time": "origin_time",
            "security": "security",
            "magnitude": "magunitude",
            "report_number": "report_num",
            "request_hypocenter_type": "request_hypo_type",
            "report_id": "report_id",
            "alert_flag": "alertflg",
        }


class KmoniReturnHypocenterModel(BaseModel):
    name: str
    longitude: str
    latitude: str
    depth: str


class KmoniReturnAreaColoringModel(BaseModel):
    areas: dict[str, AreaIntensityModel]
    recommended_areas: bool


class EEWCancelledModel(BaseModel):
    status: int = 0
    is_cancel: bool = True


class EEWParseReturnModel(BaseModel):
    status: int
    type: str
    is_plum: bool
    is_cancel: bool
    is_test: bool
    max_intensity: EEWConvertedIntensityEnum
    report_time: str
    report_timestamp: int
    report_num: int
    report_flag: EEWAlertTypeEnum
    report_id: str
    is_final: bool
    magnitude: str
    hypocenter: KmoniReturnHypocenterModel
    area_intensity: Optional[dict[str, StationIntensityModel]]
    area_coloring: KmoniReturnAreaColoringModel
    s_wave: Optional[float]
    p_wave: Optional[float]


class EEWReturnModel(BaseModel):
    kmoni: Optional[EEWParseReturnModel]
    svir: Optional[EEWParseReturnModel | EEWCancelledModel]
