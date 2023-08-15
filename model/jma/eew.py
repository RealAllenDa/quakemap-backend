from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field

from model.eew.eew_svir import SvirForecastInt, SvirForecastLgInt
from model.jma.tsunami_expectation import JMAEarthquakeHypocenterCoordinateModel, JMAEarthquakeHypocenterCodeModel, \
    JMAEarthquakeHypocenterMagnitudeModel, JMAControlModel, JMAHeadModel, JMAWarningCommentModel, JMANameCodeModel


class JMAEEWLandSea(str, Enum):
    land = "内陸"
    sea = "海域"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAEEWLandSea.unknown


class JMAEEWEarthquakeHypocenterArea(BaseModel):
    name: str = Field(validation_alias="Name")
    code: JMAEarthquakeHypocenterCodeModel = Field(validation_alias="Code")
    coordinate: JMAEarthquakeHypocenterCoordinateModel = Field(validation_alias="jmx_eb:Coordinate")
    reduced_name: Optional[str] = Field(None, validation_alias="ReduceName")
    reduced_code: Optional[JMAEarthquakeHypocenterCodeModel] = Field(None, validation_alias="ReduceCode")
    land_or_sea: Optional[JMAEEWLandSea] = Field(None, validation_alias="LandOrSea")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWEarthquakeHypocenter(BaseModel):
    area: JMAEEWEarthquakeHypocenterArea = Field(validation_alias="Area")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWEarthquake(BaseModel):
    origin_time: Optional[datetime] = Field(None, validation_alias="OriginTime")
    condition: Optional[str] = Field(None, validation_alias="Condition")
    arrival_time: datetime = Field(validation_alias="ArrivalTime")
    hypocenter: JMAEEWEarthquakeHypocenter = Field(validation_alias="Hypocenter")
    magnitude: JMAEarthquakeHypocenterMagnitudeModel = Field(validation_alias="jmx_eb:Magnitude")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWForecastKind(BaseModel):
    kind: JMANameCodeModel = Field(validation_alias="Kind")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWAreaDetail(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    forecast_kind: JMAEEWForecastKind = Field(validation_alias="Category")
    forecast_intensity: SvirForecastInt = Field(validation_alias="ForecastInt")
    forecast_long_period_intensity: Optional[SvirForecastLgInt] = Field(None, validation_alias="ForecastLgInt")
    arrival_time: Optional[datetime] = Field(None, validation_alias="ArrivalTime")
    condition: Optional[str] = Field(None, validation_alias="Condition")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWAreaIntensity(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    area: JMAEEWAreaDetail = Field(validation_alias="Area")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWIntensityForecast(BaseModel):
    # CodeDefine omitted
    forecast_intensity: SvirForecastInt = Field(validation_alias="ForecastInt")
    # Appendix omitted
    forecast_long_period_intensity: Optional[SvirForecastLgInt] = Field(None, validation_alias="ForecastLgInt")
    areas: Optional[list[JMAEEWAreaIntensity] | JMAEEWAreaIntensity] = Field(None, validation_alias="Pref")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWIntensity(BaseModel):
    forecast: Optional[JMAEEWIntensityForecast] = Field(None, validation_alias="Forecast")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWComments(BaseModel):
    warning_comment: Optional[JMAWarningCommentModel] = Field(None, validation_alias="WarningComment")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWBody(BaseModel):
    earthquake: Optional[JMAEEWEarthquake] = Field(None, validation_alias="Earthquake")
    intensity: Optional[JMAEEWIntensity] = Field(None, validation_alias="Intensity")
    text: Optional[str] = Field(None, validation_alias="Text")
    comments: Optional[JMAEEWComments] = Field(None, validation_alias="Comments")
    next_advisory: Optional[str] = Field(None, validation_alias="NextAdvisory")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWModel(BaseModel):
    control: JMAControlModel = Field(validation_alias="Control")
    head: JMAHeadModel = Field(validation_alias="Head")
    body: JMAEEWBody = Field(validation_alias="Body")
    model_config = ConfigDict(populate_by_name=True)


class JMAEEWApiModel(BaseModel):
    report: JMAEEWModel = Field(validation_alias="Report")
    model_config = ConfigDict(populate_by_name=True)
