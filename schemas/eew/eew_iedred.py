__all__ = ["IedredEEWModel", "IedredParseStatus", "IedredCodeStringDetail", "IedredMagnitude",
           "IedredTime", "IedredHypocenter", "IedredLocation", "IedredEpicenterDepth",
           "IedredMaxIntensity", "IedredEventType", "IedredEventTypeEnum",
           "IedredForecastAreasArrival", "IedredForecastAreas", "IedredForecastAreasIntensity"]

from enum import Enum
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field

from schemas.eew import EEWIntensityEnum
from schemas.eew.eew_svir import SvirLgIntensityEnum

Unknown = str


class IedredTypeEnum(str, Enum):
    warning = "緊急地震速報（警報）"
    forecast = "緊急地震速報（予報）"


class IedredEventTypeEnum(str, Enum):
    final = 9
    not_final = 0


class IedredTime(BaseModel):
    time_string: str = Field(validation_alias="String")
    unix_time: int = Field(validation_alias="UnixTime")
    rfc_time: Optional[str] = Field(None, validation_alias="RFC1123")
    model_config = ConfigDict(populate_by_name=True)


class IedredCodeString(BaseModel):
    code: int = Field(validation_alias="Code")
    string: str = Field(validation_alias="String")
    model_config = ConfigDict(populate_by_name=True)


class IedredEpicenter(BaseModel):
    code: int = Field(validation_alias="Code")
    string: str = Field(validation_alias="String")
    trust_rank: int = Field(validation_alias="Rank2")
    trust_string: str = Field(validation_alias="String2")
    model_config = ConfigDict(populate_by_name=True)


class IedredAccuracy(BaseModel):
    epicenter: IedredEpicenter = Field(validation_alias="Epicenter")
    depth: IedredCodeString = Field(validation_alias="Depth")
    magnitude: IedredCodeString = Field(validation_alias="Magnitude")
    magnitude_calculated_times: int = Field(validation_alias="NumberOfMagnitudeCalculation")
    model_config = ConfigDict(populate_by_name=True)


class IedredEpicenterDepth(BaseModel):
    depth_int: int = Field(validation_alias="Int")
    depth_string: str = Field(validation_alias="String")
    model_config = ConfigDict(populate_by_name=True)


class IedredLocation(BaseModel):
    latitude: float = Field(validation_alias="Lat")
    longitude: float = Field(validation_alias="Long")
    depth: IedredEpicenterDepth = Field(validation_alias="Depth")
    model_config = ConfigDict(populate_by_name=True)


class IedredMagnitude(BaseModel):
    magnitude_float: float | Unknown = Field(validation_alias="Float")
    magnitude_string: Optional[str] = Field(None, validation_alias="String")
    magnitude_long_string: Optional[str] = Field(None, validation_alias="LongString")
    model_config = ConfigDict(populate_by_name=True)


class IedredHypocenter(BaseModel):
    code: str = Field(validation_alias="Code")
    name: str = Field(validation_alias="Name")
    is_assumption: bool = Field(validation_alias="isAssumption")
    location: IedredLocation = Field(validation_alias="Location")
    magnitude: IedredMagnitude = Field(validation_alias="Magnitude")
    accuracy: Optional[IedredAccuracy] = Field(None, validation_alias="Accuracy")
    is_sea: Optional[bool] = Field(None, validation_alias="isSea")
    model_config = ConfigDict(populate_by_name=True)


class IedredMaxIntensity(BaseModel):
    lowest: EEWIntensityEnum = Field(validation_alias="From")
    highest: Optional[EEWIntensityEnum] = Field(None, validation_alias="To")
    string: Optional[int] = Field(None, validation_alias="String")
    long_string: Optional[str] = Field(None, validation_alias="LongString")
    model_config = ConfigDict(populate_by_name=True)


class IedredChange(BaseModel):
    code: int = Field(validation_alias="Code")
    string: str = Field(validation_alias="String")
    reason: IedredCodeString = Field(validation_alias="Reason")
    model_config = ConfigDict(populate_by_name=True)


class IedredOption(BaseModel):
    change: IedredChange = Field(validation_alias="Change")
    model_config = ConfigDict(populate_by_name=True)


class IedredCodeStringDetail(BaseModel):
    code: Optional[str] = Field(None, validation_alias="Code")
    string: Optional[str] = Field(None, validation_alias="String")
    detail: Optional[str] = Field(None, validation_alias="Detail")
    model_config = ConfigDict(populate_by_name=True)


class IedredEventType(BaseModel):
    code: Optional[str] = Field(None, validation_alias="Code")
    string: Optional[str] = Field(None, validation_alias="String")
    detail: Optional[str] = Field(None, validation_alias="Detail")
    model_config = ConfigDict(populate_by_name=True)


class IedredTitle(BaseModel):
    code: str = Field(validation_alias="Code")
    string: IedredTypeEnum = Field(validation_alias="String")
    detail: str = Field(validation_alias="Detail")
    model_config = ConfigDict(populate_by_name=True)


class IedredWarnForecastHypocenter(BaseModel):
    code: int = Field(validation_alias="Code")
    name: str = Field(validation_alias="Name")
    model_config = ConfigDict(populate_by_name=True)


class IedredWarnForecast(BaseModel):
    hypocenter: IedredWarnForecastHypocenter = Field(validation_alias="Hypocenter")
    district: list[str] = Field(validation_alias="District")
    local_areas: list[str] = Field(validation_alias="LocalAreas")
    regions: list[str] = Field(validation_alias="Regions")
    model_config = ConfigDict(populate_by_name=True)


class IedredForecastAreasIntensity(BaseModel):
    code: str = Field(validation_alias="Code")
    name: str = Field(validation_alias="Name")
    lowest: EEWIntensityEnum = Field(validation_alias="From")
    highest: EEWIntensityEnum = Field(validation_alias="To")
    lg_intensity_lowest: Optional[SvirLgIntensityEnum] = Field(None)
    lg_intensity_highest: Optional[SvirLgIntensityEnum] = Field(None)
    description: str = Field(validation_alias="Description")
    model_config = ConfigDict(populate_by_name=True)


class IedredForecastAreasArrival(BaseModel):
    flag: Optional[bool] = Field(None, validation_alias="Flag")
    condition: Optional[str] = Field(None, validation_alias="Condition")
    time: Optional[str] = Field(None, validation_alias="Time")
    model_config = ConfigDict(populate_by_name=True)


class IedredForecastAreas(BaseModel):
    intensity: IedredForecastAreasIntensity = Field(validation_alias="Intensity")
    is_warn: bool = Field(validation_alias="Warn")
    has_arrived: IedredForecastAreasArrival = Field(validation_alias="Arrival")
    model_config = ConfigDict(populate_by_name=True)


class IedredParseStatus(str, Enum):
    success = "Success"
    failed = "Failed"


class IedredEEWModel(BaseModel):
    parse_status: IedredParseStatus = Field(validation_alias="ParseStatus")
    title: Optional[IedredCodeStringDetail] = Field(None, validation_alias="Title")
    source: Optional[IedredCodeString] = Field(None, validation_alias="Source")
    status: Optional[IedredCodeStringDetail] = Field(None, validation_alias="Status")
    announced_time: Optional[IedredTime] = Field(None, validation_alias="AnnouncedTime")
    origin_time: Optional[IedredTime] = Field(None, validation_alias="OriginTime")
    event_id: Optional[str] = Field(None, validation_alias="EventID")
    event_type: Optional[IedredEventType] = Field(None, validation_alias="Type")
    serial: Optional[str] = Field(None, validation_alias="Serial")
    hypocenter: Optional[IedredHypocenter] = Field(None, validation_alias="Hypocenter")
    max_intensity: Optional[IedredMaxIntensity] = Field(None, validation_alias="MaxIntensity")
    is_warn: Optional[bool] = Field(None, validation_alias="Warn")
    optional_arguments: Optional[IedredOption] = Field(None, validation_alias="Option")
    original_text: Optional[str] = Field(None, validation_alias="OriginalText")
    warning_area_list: Optional[IedredWarnForecast] = Field(None, validation_alias="WarnForecast")
    forecast_areas: Optional[list[IedredForecastAreas]] = Field(None, validation_alias="Forecast")
    model_config = ConfigDict(populate_by_name=True)
