__all__ = ["TsunamiExpectationReturnModel", "TsunamiParseOrigin", "TsunamiExpectationModel",
           "TsunamiExpectationGrade", "TsunamiExpectationSpecialTimeModel", "TsunamiExpectationTimeModel",
           "TsunamiExpectationHeight", "TsunamiObservationReturnModel", "TsunamiObservationAreaModel",
           "TsunamiObservationCondition", "TsunamiObservationHeightCondition", "TsunamiTotalInfoModel"]

from enum import Enum
from typing import Optional, Literal

from pydantic import BaseModel, Field

from model.p2p_info import TsunamiReturnModel


class TsunamiExpectationGrade(str, Enum):
    major_warning = "MajorWarning"
    warning = "Warning"
    watch = "Watch"
    forecast = "Forecast"
    unknown = "Unknown"


class TsunamiExpectationHeight(str, Enum):
    huge = "HUGE"
    high = "HIGH"

    ten_m_above = "10<span class='indicator'>m</span> Above"
    ten_m = "10<span class='indicator'>m</span>"
    five_m = "5<span class='indicator'>m</span>"
    three_m = "3<span class='indicator'>m</span>"
    one_m = "1<span class='indicator'>m</span>"
    lesser_than_two_m = "Below 0.2m"

    unknown = "Unknown"


class TsunamiExpectationSpecialTimeModel(BaseModel):
    type: Literal['no_time'] = Field("no_time", const=True)
    time: str
    status: int


class TsunamiExpectationTimeModel(BaseModel):
    type: Literal['time'] = Field("time", const=True)
    time: str
    timestamp: int


class TsunamiExpectationModel(BaseModel):
    name: str
    grade: TsunamiExpectationGrade
    height: TsunamiExpectationHeight
    time: TsunamiExpectationTimeModel | TsunamiExpectationSpecialTimeModel = Field(..., discriminator="type")


class TsunamiExpectationReturnModel(BaseModel):
    receive_time: Optional[str]
    areas: Optional[list[TsunamiExpectationModel]]
    forecast_areas: Optional[list[TsunamiExpectationModel]]
    origin: Optional[str]


class TsunamiObservationCondition(str, Enum):
    weak = "Weak"
    observing = "Observing"
    none = "None"


class TsunamiObservationHeightCondition(str, Enum):
    rising = "Rising"
    none = "None"
    unknown = "None"


class TsunamiObservationAreaModel(BaseModel):
    name: str
    height: str
    time: str
    condition: TsunamiObservationCondition
    height_condition: TsunamiObservationHeightCondition
    height_is_max: bool


class TsunamiObservationReturnModel(BaseModel):
    areas: Optional[list[TsunamiObservationAreaModel]]
    receive_time: Optional[str]


class TsunamiParseOrigin(str, Enum):
    tsunami_expectation = "TE"
    tsunami_watch = "TW"


class TsunamiTotalInfoModel(BaseModel):
    status: str
    status_forecast: str
    map: Optional[TsunamiReturnModel]
    info: TsunamiExpectationReturnModel
    watch: TsunamiObservationReturnModel
