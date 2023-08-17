from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field

from schemas.jma.generic import JMAReportBaseModel


class JMAMessageTypeEnum(str, Enum):
    tsunami_information = "VTSE41"
    tsunami_watch = "VTSE51"
    others = "others"

    @classmethod
    def _missing_(cls, value: object):
        return JMAMessageTypeEnum.others


class JMANameCodeModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiCategoryModel(BaseModel):
    kind: JMANameCodeModel = Field(validation_alias="Kind")
    last_kind: JMANameCodeModel = Field(validation_alias="LastKind")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiFirstHeightCondition(str, Enum):
    arriving_now = "ただちに津波来襲と予測"
    arrival_expected = "津波到達中と推測"
    arrived = "第１波の到達を確認"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMATsunamiFirstHeightCondition.unknown


class JMATsunamiFirstHeightModel(BaseModel):
    arrival_time: Optional[datetime] = Field(None, validation_alias="ArrivalTime")
    condition: Optional[JMATsunamiFirstHeightCondition] = Field(None, validation_alias="Condition")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiHeightDescription(str, Enum):
    huge = "巨大"
    high = "高い"

    ten_m_above = "１０ｍ超"
    ten_m = "１０ｍ"
    five_m = "５ｍ"
    three_m = "３ｍ"
    one_m = "１ｍ"
    lesser_than_two_m = "０．２ｍ未満"

    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMATsunamiHeightDescription.unknown


class JMATsunamiHeightModel(BaseModel):
    # @type omitted
    # @unit omitted
    description: JMATsunamiHeightDescription = Field(validation_alias="@description")
    detail: str = Field(validation_alias="#text")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiMaxHeightModel(BaseModel):
    # Condition omitted
    # Revise omitted
    height: JMATsunamiHeightModel = Field(validation_alias="jmx_eb:TsunamiHeight")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiForecastItem(BaseModel):
    area: JMANameCodeModel = Field(validation_alias="Area")
    category: JMATsunamiCategoryModel = Field(validation_alias="Category")
    first_height: Optional[JMATsunamiFirstHeightModel] = Field(None, validation_alias="FirstHeight")
    max_height: Optional[JMATsunamiMaxHeightModel] = Field(None, validation_alias="MaxHeight")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiForecastModel(BaseModel):
    # CodeDefine omitted
    item: JMATsunamiForecastItem | list[JMATsunamiForecastItem] = Field(validation_alias="Item")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiModel(BaseModel):
    forecast: JMATsunamiForecastModel = Field(validation_alias="Forecast")
    model_config = ConfigDict(populate_by_name=True)


class JMAEarthquakeHypocenterCodeModel(BaseModel):
    # @type omitted
    code: str = Field(validation_alias="#text")
    model_config = ConfigDict(populate_by_name=True)


class JMAEarthquakeHypocenterCoordinateModel(BaseModel):
    # @datum omitted
    description: str = Field(validation_alias="@description")
    coordinate: Optional[str] = Field(None, validation_alias="#text")
    model_config = ConfigDict(populate_by_name=True)


class JMAEarthquakeHypocenterMagnitudeModel(BaseModel):
    # @type omitted
    # @condition omitted
    description: str = Field(validation_alias="@description")
    magnitude: str = Field(None, validation_alias="#text")
    model_config = ConfigDict(populate_by_name=True)


class JMAEarthquakeHypocenterAreaModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: JMAEarthquakeHypocenterCodeModel = Field(validation_alias="Code")
    coordinate: JMAEarthquakeHypocenterCoordinateModel = Field(validation_alias="jmx_eb:Coordinate")
    detailed_name: Optional[str] = Field(None, validation_alias="DetailName")
    name_from_mark: Optional[str] = Field(None, validation_alias="NameFromMark")
    # MarkCode, Direction, Distance omitted
    source: Optional[str] = Field(None, validation_alias="Source")
    model_config = ConfigDict(populate_by_name=True)


class JMAEarthquakeHypocenterModel(BaseModel):
    area: JMAEarthquakeHypocenterAreaModel = Field(validation_alias="Area")
    model_config = ConfigDict(populate_by_name=True)


class JMAEarthquakeModel(BaseModel):
    origin_time: datetime = Field(validation_alias="OriginTime")
    arrival_time: Optional[datetime] = Field(None, validation_alias="ArrivalTime")
    hypocenter: JMAEarthquakeHypocenterModel = Field(validation_alias="Hypocenter")
    magnitude: JMAEarthquakeHypocenterMagnitudeModel = Field(validation_alias="jmx_eb:Magnitude")
    model_config = ConfigDict(populate_by_name=True)


class JMAWarningCommentModel(BaseModel):
    # @codeType omitted
    text: str = Field(validation_alias="Text")
    code: str = Field(validation_alias="Code")
    model_config = ConfigDict(populate_by_name=True)


class JMACommentModel(BaseModel):
    warning_comment: Optional[JMAWarningCommentModel] = Field(None, validation_alias="WarningComment")
    freeform_comment: Optional[str] = Field(None, validation_alias="FreeFormComment")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiBodyModel(BaseModel):
    # optional: only when cancelled
    tsunami: Optional[JMATsunamiModel] = Field(None, validation_alias="Tsunami")
    earthquake: Optional[JMAEarthquakeModel | list[JMAEarthquakeModel]] = Field(None, validation_alias="Earthquake")
    text: Optional[str] = Field(None, validation_alias="Text")
    comments: Optional[JMACommentModel] = Field(None, validation_alias="Comments")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiExpectationModel(JMAReportBaseModel):
    body: JMATsunamiBodyModel = Field(validation_alias="Body")
    model_config = ConfigDict(populate_by_name=True)


class JMATsunamiExpectationApiModel(BaseModel):
    report: JMATsunamiExpectationModel = Field(validation_alias="Report")
    model_config = ConfigDict(populate_by_name=True)
