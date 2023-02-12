__all__ = ["SvirEEWModel", "SvirEventType", "SvirForecastLgInt", "SvirForecastInt", "SvirToIntensityEnum",
           "SvirLgIntensityEnum"]

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SvirEarthquakeAccuracy(BaseModel):
    epicenter: list[str]
    depth: str
    magnitude: str
    magnitude_calculation_times: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "epicenter": "Epicenter",
            "depth": "Depth",
            "magnitude": "MagnitudeCalculation",
            "magnitude_calculation_times": "NumberOfMagnitudeCalculation"
        }


class SvirHypocenter(BaseModel):
    name: str
    code: str
    latitude: str
    longitude: str
    depth: str
    land_or_sea: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code",
            "latitude": "Lat",
            "longitude": "Lon",
            "depth": "Depth",
            "land_or_sea": "LandOrSea"
        }


class SvirEarthquake(BaseModel):
    origin_time: str
    hypocenter: SvirHypocenter
    accuracy: SvirEarthquakeAccuracy
    magnitude: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "origin_time": "OriginTime",
            "hypocenter": "Hypocenter",
            "accuracy": "Accuracy",
            "magnitude": "Magnitude"
        }


class SvirAppendix(BaseModel):
    max_intensity_change: str
    max_intensity_change_reason: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "max_intensity_change": "MaxIntChange",
            "max_intensity_change_reason": "MaxIntChangeReason"
        }


class SvirIntensityEnum(str, Enum):
    no = "不明"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five_lower = "5-"
    five_upper = "5+"
    six_lower = "6-"
    six_upper = "6+"
    seven = "7"

    @classmethod
    def _missing_(cls, value: object):
        return cls.no


class SvirToIntensityEnum(str, Enum):
    no = "不明"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five_lower = "5-"
    five_upper = "5+"
    six_lower = "6-"
    six_upper = "6+"
    seven = "7"
    above = "over"

    @classmethod
    def _missing_(cls, value: object):
        return cls.no


class SvirLgIntensityEnum(str, Enum):
    no = "不明"
    less_than_one = "0"
    one = "1"
    two = "2"
    three = "3"
    four = "4"

    @classmethod
    def _missing_(cls, value: object):
        return cls.no


class SvirLgToIntensityEnum(str, Enum):
    no = "不明"
    less_than_one = "0"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    above = "over"

    @classmethod
    def _missing_(cls, value: object):
        return cls.no


class SvirForecastInt(BaseModel):
    lowest: SvirIntensityEnum
    highest: SvirToIntensityEnum

    class Config:
        allow_population_by_field_name = True
        fields = {
            "lowest": "From",
            "highest": "To"
        }


class SvirForecastLgInt(BaseModel):
    lowest: SvirLgIntensityEnum
    highest: SvirLgToIntensityEnum

    class Config:
        allow_population_by_field_name = True
        fields = {
            "lowest": "From",
            "highest": "To"
        }


class SvirEEWType(str, Enum):
    forecast = "緊急地震速報（予報）"
    warning = "緊急地震速報（警報）"


class SvirForecastKind(BaseModel):
    name: SvirEEWType
    code: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code"
        }


class SvirAreas(BaseModel):
    name: str
    code: str
    forecast_kind: SvirForecastKind
    max_intensity: SvirIntensityEnum
    text_intensity: str
    forecast_intensity: SvirForecastInt
    arrival_time: Optional[str]
    condition: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code",
            "forecast_kind": "Kind",
            "max_intensity": "MaxInt",
            "text_intensity": "TextInt",
            "forecast_intensity": "ForecastInt",
            "arrival_time": "ArrivalTime",
            "condition": "Condition"
        }


class SvirIntensity(BaseModel):
    max_intensity: SvirIntensityEnum
    text_intensity: str
    forecast_intensity: SvirForecastInt
    areas: Optional[list[SvirAreas]]
    appendix: Optional[SvirAppendix]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "max_intensity": "MaxInt",
            "text_intensity": "TextInt",
            "forecast_intensity": "ForecastInt",
            "areas": "Areas",
            "appendix": "Appendix"
        }


class SvirBody(BaseModel):
    earthquake: Optional[SvirEarthquake]
    intensity: SvirIntensity
    is_plum: Optional[str]
    is_warn: Optional[str]
    is_end: Optional[str]
    comments: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "earthquake": "Earthquake",
            "intensity": "Intensity",
            "is_plum": "PLUMFlag",
            "is_warn": "WarningFlag",
            "is_end": "EndFlag",
            "comments": "Text"
        }


class SvirEventType(str, Enum):
    normal = "通常"
    cancel = "取消"
    train = "訓練"
    train_cancel = "訓練取消"
    test = "試験"


class SvirHead(BaseModel):
    title: str = Field("緊急地震速報（予報）", const=True)
    publish_time: str
    edit_office: str
    publish_office: str = Field("気象庁", const=True)
    event_id: str
    status: SvirEventType
    serial: str
    version: str = Field("1.1", const=True)

    class Config:
        allow_population_by_field_name = True
        fields = {
            "title": "Title",
            "publish_time": "DateTime",
            "edit_office": "EditorialOffice",
            "publish_office": "PublishingOffice",
            "event_id": "EventID",
            "status": "Status",
            "serial": "Serial",
            "version": "Version"
        }


class SvirEEWModel(BaseModel):
    head: SvirHead
    body: SvirBody

    class Config:
        allow_population_by_field_name = True
        fields = {
            "head": "Head",
            "body": "Body"
        }
