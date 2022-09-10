#  CONFIDENTIAL HomeNetwork
#  Unpublished Copyright (c) 2022.
#
#  NOTICE: All information contained herein is, and remains the property of HomeNetwork.
#  Dissemination of this information or reproduction of this material is strictly forbidden unless
#  prior written permission is obtained from HomeNetwork.
from datetime import datetime
from typing import Optional

from pydantic import Field, BaseModel

from model.dmdata.generic import DmdataGenericResponse


class DmdataSocketStartBody(BaseModel):
    classifications: list[str]
    types: list[str]
    app_name: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "classifications": "classifications",
            "types": "types",
            "app_name": "appName"
        }


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
    types: Optional[list[str]]
    formats: list[str]
    # appName omitted


class DmdataSocketError(BaseModel):
    type: str = Field("error")
    error: str
    code: int
    close: bool


class DmdataPing(BaseModel):
    type: str = Field("ping")
    ping_id: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "type": "type",
            "ping_id": "pingId"
        }


class DmdataPong(BaseModel):
    type: str = "pong"
    ping_id: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "type": "type",
            "ping_id": "pingId"
        }


class DmdataSocketStart(BaseModel):
    type: str = Field("start")
    socket_id: int
    classifications: list[str]
    types: Optional[list[str]]
    test: str
    formats: list[str]
    # appName omitted
    time: datetime

    class Config:
        allow_population_by_field_name = True
        fields = {
            "type": "type",
            "socket_id": "socketId",
            "classifications": "classifications",
            "types": "types",
            "test": "test",
            "format": "format",
            "time": "time"
        }


class DmdataSocketDataPassing(BaseModel):
    name: str
    time: datetime


class DmdataSocketDataHead(BaseModel):
    type: str
    author: str
    time: datetime
    designation: Optional[str]
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
    compression: Optional[str]
    encoding: str
    body: str
