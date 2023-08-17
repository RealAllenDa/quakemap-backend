from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, AliasChoices


class JMAControlStatus(str, Enum):
    normal = "通常"
    train = "訓練"
    test = "試験"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAControlStatus.unknown


class JMAControlModel(BaseModel):
    title: str = Field(validation_alias=AliasChoices("Title", "title"))
    date: datetime = Field(validation_alias=AliasChoices("DateTime", "dateTime"))
    status: JMAControlStatus = Field(validation_alias=AliasChoices("Status", "status"))
    editorial_office: str = Field(validation_alias=AliasChoices("EditorialOffice", "editorialOffice"))
    publishing_office: str = Field(validation_alias=AliasChoices("PublishingOffice", "publishingOffice"))
    model_config = ConfigDict(populate_by_name=True)


class JMAInfoType(str, Enum):
    issued = "発表"
    correction = "訂正"
    cancel = "取消"
    unknown = ""

    @classmethod
    def _missing_(cls, value: object):
        return JMAInfoType.unknown


class JMAHeadHeadlineModel(BaseModel):
    text: Optional[str] = Field(None, validation_alias="Text")
    model_config = ConfigDict(populate_by_name=True)


class JMAHeadModel(BaseModel):
    title: str = Field(validation_alias=AliasChoices("Title", "title"))
    report_date: datetime = Field(validation_alias=AliasChoices("ReportDateTime", "reportDateTime"))
    target_date: Optional[datetime] = Field(None, validation_alias=AliasChoices("TargetDateTime", "targetDateTime"))
    event_id: str = Field(validation_alias=AliasChoices("EventID", "eventId"))
    info_status: JMAInfoType = Field(validation_alias=AliasChoices("InfoType", "infoType"))
    serial: Optional[str] = Field(None, validation_alias=AliasChoices("Serial", "serial"))
    info_type: str = Field(validation_alias=AliasChoices("InfoKind", "infoKind"))
    headline: Optional[JMAHeadHeadlineModel] | str = Field(validation_alias=AliasChoices("Headline", "headline"))
    model_config = ConfigDict(populate_by_name=True)


class JMAReportBaseModel(BaseModel):
    control: JMAControlModel = Field(validation_alias="Control")
    head: JMAHeadModel = Field(validation_alias="Head")
    model_config = ConfigDict(populate_by_name=True)
