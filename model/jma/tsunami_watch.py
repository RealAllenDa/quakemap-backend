from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from model.jma.tsunami_expectation import JMANameCodeModel, JMAHeadModel, JMAControlModel, JMACommentModel, \
    JMAEarthquakeModel, JMATsunamiForecastModel

__all__ = ["JMATsunamiWatchApiModel", "JMAWatchMaxHeightCondition"]


class JMAWatchFirstHeightCondition(str, Enum):
    cannot_identify = "第１波識別不能"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAWatchFirstHeightCondition.unknown


class JMAWatchHeightCondition(str, Enum):
    rising = "上昇中"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAWatchHeightCondition.unknown


class JMAWatchMaxHeightCondition(str, Enum):
    weak = "微弱"
    observing = "観測中"
    important = "重要"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAWatchMaxHeightCondition.unknown


class JMATsunamiWatchFirstHeightModel(BaseModel):
    # Initial omitted
    # Revise omitted
    arrival_time: Optional[datetime]
    condition: Optional[JMAWatchFirstHeightCondition]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "arrival_time": "ArrivalTime",
            "condition": "Condition"
        }


class JMAWatchTsunamiHeightModel(BaseModel):
    # @type omitted
    # @unit omitted
    condition: Optional[JMAWatchHeightCondition]
    description: str
    text: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "condition": "@condition",
            "description": "@description",
            "text": "#text"
        }


class JMATsunamiWatchMaxHeightModel(BaseModel):
    # Revise omitted
    condition: Optional[JMAWatchMaxHeightCondition]
    date: Optional[datetime]
    height: Optional[JMAWatchTsunamiHeightModel]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "condition": "Condition",
            "date": "DateTime",
            "height": "jmx_eb:TsunamiHeight"
        }


class JMATsunamiWatchStation(BaseModel):
    name: str
    code: str
    first_height: JMATsunamiWatchFirstHeightModel
    max_height: JMATsunamiWatchMaxHeightModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code",
            "first_height": "FirstHeight",
            "max_height": "MaxHeight"
        }


class JMATsunamiWatchItem(BaseModel):
    area: JMANameCodeModel
    station: JMATsunamiWatchStation | list[JMATsunamiWatchStation]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "area": "Area",
            "station": "Station"
        }


class JMATsunamiWatchObservationModel(BaseModel):
    # CodeDefine omitted
    item: JMATsunamiWatchItem | list[JMATsunamiWatchItem]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "item": "Item"
        }


class JMATsunamiWatchContentModel(BaseModel):
    observation: Optional[JMATsunamiWatchObservationModel]
    forecast: JMATsunamiForecastModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "observation": "Observation",
            "forecast": "Forecast"
        }


class JMATsunamiWatchBodyModel(BaseModel):
    # optional: only when cancelled
    tsunami: Optional[JMATsunamiWatchContentModel]
    earthquake: Optional[JMAEarthquakeModel | list[JMAEarthquakeModel]]
    text: Optional[str]
    comments: Optional[JMACommentModel]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "tsunami": "Tsunami",
            "earthquake": "Earthquake",
            "text": "Text",
            "comments": "Comments"
        }


class JMATsunamiWatchModel(BaseModel):
    control: JMAControlModel
    head: JMAHeadModel
    body: JMATsunamiWatchBodyModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "control": "Control",
            "head": "Head",
            "body": "Body"
        }


class JMATsunamiWatchApiModel(BaseModel):
    report: JMATsunamiWatchModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "report": "Report"
        }
