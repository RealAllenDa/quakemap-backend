from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from model.eew.eew_svir import SvirForecastInt
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
    name: str
    code: JMAEarthquakeHypocenterCodeModel
    coordinate: JMAEarthquakeHypocenterCoordinateModel
    reduced_name: Optional[str]
    reduced_code: Optional[JMAEarthquakeHypocenterCodeModel]
    land_or_sea: Optional[JMAEEWLandSea]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code",
            "coordinate": "jmx_eb:Coordinate",
            "reduced_name": "ReduceName",
            "reduced_code": "ReduceCode",
            "land_or_sea": "LandOrSea"
        }


class JMAEEWEarthquakeHypocenter(BaseModel):
    area: JMAEEWEarthquakeHypocenterArea

    # Accuracy omitted

    class Config:
        allow_population_by_field_name = True
        fields = {
            "area": "Area"
        }


class JMAEEWEarthquake(BaseModel):
    origin_time: Optional[datetime]
    condition: Optional[str]
    arrival_time: Optional[datetime]
    hypocenter: JMAEEWEarthquakeHypocenter
    magnitude: JMAEarthquakeHypocenterMagnitudeModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "origin_time": "OriginTime",
            "condition": "Condition",
            "arrival_time": "ArrivalTime",
            "hypocenter": "Hypocenter",
            "magnitude": "jmx_eb:Magnitude"
        }


class JMAEEWForecastKind(BaseModel):
    kind: JMANameCodeModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "kind": "Kind"
        }


class JMAEEWAreaDetail(BaseModel):
    name: str
    code: str
    forecast_kind: JMAEEWForecastKind
    forecast_intensity: SvirForecastInt
    arrival_time: Optional[datetime]
    condition: Optional[str]

    # TODO ForecastLgInt

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code",
            "forecast_kind": "Category",
            "forecast_intensity": "ForecastInt",
            "arrival_time": "ArrivalTime",
            "condition": "Condition"
        }


class JMAEEWAreaIntensity(BaseModel):
    name: str
    code: str
    area: JMAEEWAreaDetail

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code",
            "area": "Area"
        }


class JMAEEWIntensityForecast(BaseModel):
    # CodeDefine omitted
    forecast_intensity: SvirForecastInt
    # Appendix omitted
    # TODO ForecastLgInt implement
    areas: Optional[list[JMAEEWAreaIntensity] | JMAEEWAreaIntensity]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "forecast_intensity": "ForecastInt",
            "areas": "Pref"
        }


class JMAEEWIntensity(BaseModel):
    forecast: Optional[JMAEEWIntensityForecast]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "forecast": "Forecast"
        }


class JMAEEWComments(BaseModel):
    warning_comment: Optional[JMAWarningCommentModel]
    next_advisory: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "warning_comment": "WarningComment",
            "next_advisory": "NextAdvisory"
        }


class JMAEEWBody(BaseModel):
    earthquake: Optional[JMAEEWEarthquake]
    intensity: Optional[JMAEEWIntensity]
    text: Optional[str]
    comments: Optional[JMAEEWComments]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "earthquake": "Earthquake",
            "intensity": "Intensity",
            "text": "Text",
            "comments": "Comments"
        }


class JMAEEWModel(BaseModel):
    control: JMAControlModel
    head: JMAHeadModel
    body: JMAEEWBody

    class Config:
        allow_population_by_field_name = True
        fields = {
            "control": "Control",
            "head": "Head",
            "body": "Body"
        }


class JMAEEWApiModel(BaseModel):
    report: JMAEEWModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "report": "Report"
        }
