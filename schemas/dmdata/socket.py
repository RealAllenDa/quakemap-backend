from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field, BaseModel

from schemas.dmdata.generic import DmdataGenericResponse, DmdataMessageTypes
from schemas.jma.generic import JMAReportBaseModel


class DmdataSocketStartBody(BaseModel):
    classifications: list[str]
    types: list[str]
    app_name: str = Field(validation_alias="appName")
    model_config = ConfigDict(populate_by_name=True)


class DmdataSocketModel(BaseModel):
    id: int
    url: str
    # protocol omitted
    expiration: int


class DmdataSocketStartResponse(DmdataGenericResponse):
    status: str = Field("ok")
    ticket: str
    websocket: DmdataSocketModel
    classifications: list[str]
    test: str
    types: Optional[list[str]] = None
    formats: list[str]
    # appName omitted


class DmdataSocketError(BaseModel):
    type: str = Field("error")
    error: str
    code: int
    close: bool


class DmdataPing(BaseModel):
    type: str = Field("ping")
    ping_id: str = Field(validation_alias="pingId")
    model_config = ConfigDict(populate_by_name=True)


class DmdataPong(BaseModel):
    type: str = "pong"
    ping_id: str = Field(validation_alias="pingId")
    model_config = ConfigDict(populate_by_name=True)


class DmdataSocketStart(BaseModel):
    type: str = Field("start")
    socket_id: int = Field(validation_alias="socketId")
    classifications: list[str]
    types: Optional[list[str]] = None
    test: str
    formats: list[str]
    # appName omitted
    time: datetime
    model_config = ConfigDict(populate_by_name=True)


class DmdataSocketDataPassing(BaseModel):
    name: str
    time: datetime


class DmdataSocketDataHead(BaseModel):
    type: DmdataMessageTypes
    author: str
    time: datetime
    designation: Optional[str] = None
    test: bool
    xml: bool


class DmdataSocketData(BaseModel):
    type: str = Field("data")
    version: str
    id: str
    classification: str
    passing: list[DmdataSocketDataPassing]
    head: DmdataSocketDataHead
    xmlReport: Optional[JMAReportBaseModel] = None
    format: str
    compression: Optional[str] = None
    encoding: str
    body: str
