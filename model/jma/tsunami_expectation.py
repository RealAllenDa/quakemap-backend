from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Optional


class JMAMessageTypeEnum(str, Enum):
    tsunami_information = "VTSE41"
    tsunami_watch = "VTSE51"
    others = "others"

    @classmethod
    def _missing_(cls, value: object):
        return JMAMessageTypeEnum.others


class JMAControlStatus(str, Enum):
    normal = "通常"
    train = "訓練"
    test = "試験"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAControlStatus.unknown


class JMAControlModel(BaseModel):
    title: str
    date: datetime
    status: JMAControlStatus
    editorial_office: str
    publishing_office: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "title": "Title",
            "date": "DateTime",
            "status": "Status",
            "editorial_office": "EditorialOffice",
            "publishing_office": "PublishingOffice"
        }


class JMAInfoType(str, Enum):
    issued = "発表"
    correction = "訂正"
    cancel = "取消"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAInfoType.unknown


class JMAHeadHeadlineModel(BaseModel):
    text: Optional[str]

    # Information omitted

    class Config:
        allow_population_by_field_name = True
        fields = {
            "text": "Text"
        }


class JMAHeadModel(BaseModel):
    title: str
    report_date: datetime
    target_date: Optional[datetime]
    event_id: str
    info_status: JMAInfoType
    serial: Optional[str]
    info_type: str
    headline: JMAHeadHeadlineModel

    # InfoKindVersion omitted

    class Config:
        allow_population_by_field_name = True
        fields = {
            "title": "Title",
            "report_date": "ReportDateTime",
            "target_date": "TargetDateTime",
            "event_id": "EventID",
            "info_status": "InfoType",
            "serial": "Serial",
            "info_type": "InfoKind",
            "headline": "Headline"
        }


class JMANameCodeModel(BaseModel):
    name: str
    code: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code"
        }


class JMATsunamiCategoryModel(BaseModel):
    kind: JMANameCodeModel
    last_kind: JMANameCodeModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "kind": "Kind",
            "last_kind": "LastKind"
        }


class JMATsunamiFirstHeightCondition(str, Enum):
    arriving_now = "ただちに津波来襲と予測"
    arrival_expected = "津波到達中と推測"
    arrived = "第１波の到達を確認"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMATsunamiFirstHeightCondition.unknown


class JMATsunamiFirstHeightModel(BaseModel):
    arrival_time: Optional[datetime]
    condition: Optional[JMATsunamiFirstHeightCondition]

    # Revise omitted

    class Config:
        allow_population_by_field_name = True
        fields = {
            "arrival_time": "ArrivalTime",
            "condition": "Condition"
        }


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
    description: JMATsunamiHeightDescription
    detail: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "description": "@description",
            "detail": "#text"
        }


class JMATsunamiMaxHeightModel(BaseModel):
    # Condition omitted
    # Revise omitted
    height: JMATsunamiHeightModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "height": "jmx_eb:TsunamiHeight"
        }


class JMATsunamiForecastItem(BaseModel):
    area: JMANameCodeModel
    category: JMATsunamiCategoryModel
    first_height: Optional[JMATsunamiFirstHeightModel]
    max_height: Optional[JMATsunamiMaxHeightModel]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "area": "Area",
            "category": "Category",
            "first_height": "FirstHeight",
            "max_height": "MaxHeight"
        }


class JMATsunamiForecastModel(BaseModel):
    # CodeDefine omitted
    item: JMATsunamiForecastItem | list[JMATsunamiForecastItem]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "item": "Item"
        }


class JMATsunamiModel(BaseModel):
    forecast: JMATsunamiForecastModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "forecast": "Forecast"
        }


class JMAEarthquakeHypocenterCodeModel(BaseModel):
    # @type omitted
    code: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "code": "#text"
        }


class JMAEarthquakeHypocenterCoordinateModel(BaseModel):
    # @datum omitted
    description: str
    coordinate: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "description": "@description",
            "coordinate": "#text"
        }


class JMAEarthquakeHypocenterMagnitudeModel(BaseModel):
    # @type omitted
    # @condition omitted
    description: str
    magnitude: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "description": "@description",
            "magnitude": "#text"
        }


class JMAEarthquakeHypocenterAreaModel(BaseModel):
    name: str
    code: JMAEarthquakeHypocenterCodeModel
    coordinate: JMAEarthquakeHypocenterCoordinateModel
    detailed_name: Optional[str]
    name_from_mark: Optional[str]
    # MarkCode, Direction, Distance omitted
    source: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "name": "Name",
            "code": "Code",
            "coordinate": "jmx_eb:Coordinate",
            "detailed_name": "DetailName",
            "name_from_mark": "NameFromMark",
            "source": "Source"
        }


class JMAEarthquakeHypocenterModel(BaseModel):
    area: JMAEarthquakeHypocenterAreaModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "area": "Area"
        }


class JMAEarthquakeModel(BaseModel):
    origin_time: datetime
    arrival_time: Optional[datetime]
    hypocenter: JMAEarthquakeHypocenterModel
    magnitude: JMAEarthquakeHypocenterMagnitudeModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "origin_time": "OriginTime",
            "arrival_time": "ArrivalTime",
            "hypocenter": "Hypocenter",
            "magnitude": "jmx_eb:Magnitude"
        }


class JMAWarningCommentModel(BaseModel):
    # @codeType omitted
    text: str
    code: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "text": "Text",
            "code": "Code"
        }


class JMACommentModel(BaseModel):
    warning_comment: Optional[JMAWarningCommentModel]
    freeform_comment: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "warning_comment": "WarningComment",
            "freeform_comment": "FreeFormComment"
        }


class JMATsunamiBodyModel(BaseModel):
    # optional: only when cancelled
    tsunami: Optional[JMATsunamiModel]
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


class JMATsunamiExpectationModel(BaseModel):
    control: JMAControlModel
    head: JMAHeadModel
    body: JMATsunamiBodyModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "control": "Control",
            "head": "Head",
            "body": "Body"
        }


class JMATsunamiExpectationApiModel(BaseModel):
    report: JMATsunamiExpectationModel

    class Config:
        allow_population_by_field_name = True
        fields = {
            "report": "Report"
        }
