from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field

from schemas.jma.generic import JMAReportBaseModel
from schemas.jma.tsunami_expectation import JMANameCodeModel, JMACommentModel, \
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
    arrival_time: Optional[datetime] = Field(None, validation_alias="ArrivalTime")
    condition: Optional[JMAWatchFirstHeightCondition] = Field(None, validation_alias="Condition")
    model_config = ConfigDict(populate_by_name=True)


class JMAWatchTsunamiHeightModel(BaseModel):
    # @type omitted
    # @unit omitted
    condition: Optional[JMAWatchHeightCondition] = Field(None, validation_alias="@condition")
    description: str = Field(validation_alias="@description")
    text: str = Field(validation_alias="#text")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchMaxHeightModel(BaseModel):
    # Revise omitted
    condition: Optional[JMAWatchMaxHeightCondition] = Field(None, validation_alias="Condition")
    date: Optional[datetime] = Field(None, validation_alias="DateTime")
    height: Optional[JMAWatchTsunamiHeightModel] = Field(None, validation_alias="jmx_eb:TsunamiHeight")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchStation(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    first_height: JMATsunamiWatchFirstHeightModel = Field(JMATsunamiWatchFirstHeightModel(),
                                                          validation_alias="FirstHeight")
    max_height: JMATsunamiWatchMaxHeightModel = Field(JMATsunamiWatchMaxHeightModel(),
                                                      validation_alias="MaxHeight")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchItem(BaseModel):
    area: JMANameCodeModel = Field(validation_alias="Area")
    station: JMATsunamiWatchStation | list[JMATsunamiWatchStation] = Field(validation_alias="Station")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchObservationModel(BaseModel):
    # CodeDefine omitted
    item: JMATsunamiWatchItem | list[JMATsunamiWatchItem] = Field(validation_alias="Item")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchContentModel(BaseModel):
    observation: Optional[JMATsunamiWatchObservationModel] = Field(None, validation_alias="Observation")
    forecast: JMATsunamiForecastModel = Field(validation_alias="Forecast")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchBodyModel(BaseModel):
    # optional: only when cancelled
    tsunami: Optional[JMATsunamiWatchContentModel] = Field(None, validation_alias="Tsunami")
    earthquake: Optional[JMAEarthquakeModel | list[JMAEarthquakeModel]] = Field(None, validation_alias="Earthquake")
    text: Optional[str] = Field(None, validation_alias="Text")
    comments: Optional[JMACommentModel] = Field(None, validation_alias="Comments")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchModel(JMAReportBaseModel):
    body: JMATsunamiWatchBodyModel = Field(validation_alias="Body")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiWatchApiModel(BaseModel):
    report: JMATsunamiWatchModel = Field(validation_alias="Report")
    model_config = ConfigDict(populate_by_name=True)
