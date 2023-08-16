from datetime import datetime
from typing import Optional

from pydantic import Field, BaseModel

from model.dmdata.generic import DmdataGenericResponse, DmdataMessageTypes


class DmdataSocketStartBody(BaseModel):
    classifications: list[str]
    types: list[str]
    app_name: str = Field(alias="appName")


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
    ping_id: str = Field(alias="pingId")


class DmdataPong(BaseModel):
    type: str = "pong"
    ping_id: str = Field(alias="pingId")


class DmdataSocketStart(BaseModel):
    type: str = Field("start")
    socket_id: int = Field(alias="socketId")
    classifications: list[str]
    types: Optional[list[str]] = None
    test: str
    formats: list[str]
    # appName omitted
    time: datetime


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
    # xmlReport omitted
    format: str
    compression: Optional[str] = None
    encoding: str
    body: str
