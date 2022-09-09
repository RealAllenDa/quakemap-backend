__all__ = ["IedredEEWModel", "IedredParseStatus", "IedredCodeStringDetail", "IedredMagnitude",
           "IedredTime", "IedredHypocenter", "IedredLocation", "IedredEpicenterDepth",
           "IedredMaxIntensity", "IedredEventType", "IedredEventTypeEnum",
           "IedredForecastAreasArrival", "IedredForecastAreas", "IedredForecastAreasIntensity"]

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from model.eew import EEWIntensityEnum

Unknown = str


class IedredTypeEnum(str, Enum):
    warning = "緊急地震速報（警報）"
    forecast = "緊急地震速報（予報）"


class IedredEventTypeEnum(str, Enum):
    final = 9
    not_final = 0


class IedredTime(BaseModel):
    time_string: str
    unix_time: int
    rfc_time: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "time_string": "String",
            "unix_time": "UnixTime",
            "rfc_time": "RFC1123"
        }


class IedredCodeString(BaseModel):
    code: int
    string: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "string": "String"
        }


class IedredEpicenter(BaseModel):
    code: int
    string: str
    trust_rank: int
    trust_string: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "string": "String",
            "trust_rank": "Rank2",
            "trust_string": "String2"
        }


class IedredAccuracy(BaseModel):
    epicenter: IedredEpicenter
    depth: IedredCodeString
    magnitude: IedredCodeString
    magnitude_calculated_times: int

    class Config:
        allow_population_by_field_name = True
        fields = {
            "epicenter": "Epicenter",
            "depth": "Depth",
            "magnitude": "Magnitude",
            "magnitude_calculated_times": "NumberOfMagnitudeCalculation"
        }


class IedredEpicenterDepth(BaseModel):
    depth_int: int
    depth_string: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "depth_int": "Int",
            "depth_string": "String",
        }


class IedredLocation(BaseModel):
    latitude: float
    longitude: float
    depth: IedredEpicenterDepth

    class Config:
        allow_population_by_field_name = True
        fields = {
            "latitude": "Lat",
            "longitude": "Long",
            "depth": "Depth"
        }


class IedredMagnitude(BaseModel):
    magnitude_float: float | Unknown
    magnitude_string: Optional[str]
    magnitude_long_string: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "magnitude_float": "Float",
            "magnitude_string": "String",
            "magnitude_long_string": "LongString"
        }


class IedredHypocenter(BaseModel):
    code: str
    name: str
    is_assumption: bool
    location: IedredLocation
    magnitude: IedredMagnitude
    accuracy: Optional[IedredAccuracy]
    is_sea: Optional[bool]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "name": "Name",
            "is_assumption": "isAssumption",
            "location": "Location",
            "magnitude": "Magnitude",
            "accuracy": "Accuracy",
            "is_sea": "isSea"
        }


class IedredMaxIntensity(BaseModel):
    lowest: EEWIntensityEnum
    highest: Optional[EEWIntensityEnum]
    string: Optional[int]
    long_string: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "lowest": "From",
            "highest": "To",
            "string": "String",
            "long_string": "LongString"
        }


class IedredChange(BaseModel):
    code: int
    string: str
    reason: IedredCodeString

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "string": "String",
            "reason": "Reason"
        }


class IedredOption(BaseModel):
    change: IedredChange

    class Config:
        allow_population_by_field_name = True
        fields = {
            "change": "Change"
        }


class IedredCodeStringDetail(BaseModel):
    code: Optional[str]
    string: Optional[str]
    detail: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "string": "String",
            "detail": "Detail"
        }


class IedredEventType(BaseModel):
    code: Optional[str]
    string: Optional[str]
    detail: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "string": "String",
            "detail": "Detail"
        }


class IedredTitle(BaseModel):
    code: str
    string: IedredTypeEnum
    detail: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "string": "String",
            "detail": "Detail"
        }


class IedredWarnForecastHypocenter(BaseModel):
    code: int
    name: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "name": "Name"
        }


class IedredWarnForecast(BaseModel):
    hypocenter: IedredWarnForecastHypocenter
    district: list[str]
    local_areas: list[str]
    regions: list[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "hypocenter": "Hypocenter",
            "district": "District",
            "local_areas": "LocalAreas",
            "regions": "Regions"
        }


class IedredForecastAreasIntensity(BaseModel):
    code: str
    name: str
    lowest: EEWIntensityEnum
    highest: EEWIntensityEnum
    description: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "Code",
            "name": "Name",
            "lowest": "From",
            "highest": "To",
            "description": "Description"
        }


class IedredForecastAreasArrival(BaseModel):
    flag: Optional[bool] = None
    condition: Optional[str]
    time: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        fields = {
            "flag": "Flag",
            "condition": "Condition",
            "time": "Time"
        }


class IedredForecastAreas(BaseModel):
    intensity: IedredForecastAreasIntensity
    is_warn: bool
    has_arrived: IedredForecastAreasArrival

    class Config:
        allow_population_by_field_name = True
        fields = {
            "intensity": "Intensity",
            "is_warn": "Warn",
            "has_arrived": "Arrival"
        }


class IedredParseStatus(str, Enum):
    success = "Success"
    failed = "Failed"


class IedredEEWModel(BaseModel):
    parse_status: IedredParseStatus
    title: Optional[IedredCodeStringDetail]
    source: Optional[IedredCodeString]
    status: Optional[IedredCodeStringDetail]
    announced_time: Optional[IedredTime]
    origin_time: Optional[IedredTime]
    event_id: Optional[str]
    event_type: Optional[IedredEventType]
    serial: Optional[str]
    hypocenter: Optional[IedredHypocenter]
    max_intensity: Optional[IedredMaxIntensity]
    is_warn: Optional[bool]
    optional_arguments: Optional[IedredOption]
    original_text: Optional[str]
    warning_area_list: Optional[IedredWarnForecast]
    forecast_areas: Optional[list[IedredForecastAreas]]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "parse_status": "ParseStatus",
            "title": "Title",
            "source": "Source",
            "status": "Status",
            "announced_time": "AnnouncedTime",
            "origin_time": "OriginTime",
            "event_id": "EventID",
            "event_type": "Type",
            "serial_id": "Serial",
            "hypocenter": "Hypocenter",
            "max_intensity": "MaxIntensity",
            "is_warn": "Warn",
            "optional_arguments": "Option",
            "original_text": "OriginalText",
            "warning_area_list": "WarnForecast",
            "forecast_areas": "Forecast"
        }
