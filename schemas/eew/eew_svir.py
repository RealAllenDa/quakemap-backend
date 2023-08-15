__all__ = ["SvirEEWModel", "SvirEventType", "SvirForecastLgInt", "SvirForecastInt", "SvirToIntensityEnum",
           "SvirLgIntensityEnum", "SvirLgToIntensityEnum"]

from enum import Enum
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field


class SvirEarthquakeAccuracy(BaseModel):
    epicenter: list[str] = Field(validation_alias="Epicenter")
    depth: str = Field(validation_alias="Depth")
    magnitude: str = Field(validation_alias="MagnitudeCalculation")
    magnitude_calculation_times: str = Field(validation_alias="NumberOfMagnitudeCalculation")
    model_config = ConfigDict(populate_by_name=True)


class SvirHypocenter(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    latitude: str = Field(validation_alias="Lat")
    longitude: str = Field(validation_alias="Lon")
    depth: str = Field(validation_alias="Depth")
    land_or_sea: Optional[str] = Field(None, validation_alias="LandOrSea")
    model_config = ConfigDict(populate_by_name=True)


class SvirEarthquake(BaseModel):
    origin_time: str = Field(validation_alias="OriginTime")
    hypocenter: SvirHypocenter = Field(validation_alias="Hypocenter")
    accuracy: SvirEarthquakeAccuracy = Field(validation_alias="Accuracy")
    magnitude: str = Field(validation_alias="Magnitude")
    model_config = ConfigDict(populate_by_name=True)


class SvirAppendix(BaseModel):
    max_intensity_change: str = Field(validation_alias="MaxIntChange")
    max_intensity_change_reason: str = Field(validation_alias="MaxIntChangeReason")
    model_config = ConfigDict(populate_by_name=True)


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
    lowest: SvirIntensityEnum = Field(validation_alias="From")
    highest: SvirToIntensityEnum = Field(validation_alias="To")
    model_config = ConfigDict(populate_by_name=True)


class SvirForecastLgInt(BaseModel):
    lowest: SvirLgIntensityEnum = Field(validation_alias="From")
    highest: SvirLgToIntensityEnum = Field(validation_alias="To")
    model_config = ConfigDict(populate_by_name=True)


class SvirEEWType(str, Enum):
    forecast = "緊急地震速報（予報）"
    warning = "緊急地震速報（警報）"


class SvirForecastKind(BaseModel):
    name: SvirEEWType = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    model_config = ConfigDict(populate_by_name=True)


class SvirAreas(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    forecast_kind: SvirForecastKind = Field(validation_alias="Kind")
    max_intensity: SvirIntensityEnum = Field(validation_alias="MaxInt")
    text_intensity: str = Field(validation_alias="TextInt")
    forecast_intensity: SvirForecastInt = Field(validation_alias="ForecastInt")
    arrival_time: Optional[str] = Field(None, validation_alias="ArrivalTime")
    condition: Optional[str] = Field(None, validation_alias="Condition")
    model_config = ConfigDict(populate_by_name=True)


class SvirIntensity(BaseModel):
    max_intensity: SvirIntensityEnum = Field(validation_alias="MaxInt")
    text_intensity: str = Field(validation_alias="TextInt")
    forecast_intensity: SvirForecastInt = Field(validation_alias="ForecastInt")
    areas: Optional[list[SvirAreas]] = Field(None, validation_alias="Areas")
    appendix: Optional[SvirAppendix] = Field(None, validation_alias="Appendix")
    model_config = ConfigDict(populate_by_name=True)


class SvirBody(BaseModel):
    earthquake: Optional[SvirEarthquake] = Field(None, validation_alias="Earthquake")
    intensity: SvirIntensity = Field(validation_alias="Intensity")
    is_plum: Optional[str] = Field(None, validation_alias="PLUMFlag")
    is_warn: Optional[str] = Field(None, validation_alias="WarningFlag")
    is_end: Optional[str] = Field(None, validation_alias="EndFlag")
    comments: Optional[str] = Field(None, validation_alias="Text")
    model_config = ConfigDict(populate_by_name=True)


class SvirEventType(str, Enum):
    normal = "通常"
    cancel = "取消"
    train = "訓練"
    train_cancel = "訓練取消"
    test = "試験"


class SvirHead(BaseModel):
    title: str = Field(validation_alias="Title")
    publish_time: str = Field(validation_alias="DateTime")
    edit_office: str = Field(validation_alias="EditorialOffice")
    publish_office: str = Field(validation_alias="PublishingOffice")
    event_id: str = Field(validation_alias="EventID")
    status: SvirEventType = Field(validation_alias="Status")
    serial: str = Field(validation_alias="Serial")
    version: str = Field(validation_alias="Version")
    model_config = ConfigDict(populate_by_name=True)


class SvirEEWModel(BaseModel):
    head: SvirHead = Field(validation_alias="Head")
    body: SvirBody = Field(validation_alias="Body")
    model_config = ConfigDict(populate_by_name=True)
