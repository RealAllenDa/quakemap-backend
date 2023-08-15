from enum import Enum
from typing import Optional

from pydantic import ConfigDict, BaseModel, Field


class DmdataMessageTypes(str, Enum):
    eew_forecast = "VXSE44"
    eew_warning = "VXSE43"

    eq_intensity_report = "VXSE51"
    eq_destination = "VXSE52"
    eq_intensity_destination = "VXSE53"
    eq_destination_change = "VXSE61"

    tsunami_warning = "VTSE41"
    tsunami_info = "VTSE51"


class DmdataGenericErrorModel(BaseModel):
    error: str
    error_description: str


class DmdataGenericResponse(BaseModel):
    response_id: str = Field(validation_alias="responseId")
    response_time: str = Field(validation_alias="responseTime")
    status: str
    model_config = ConfigDict(populate_by_name=True)


class DmdataErrorModel(BaseModel):
    message: str
    code: int


class DmdataGenericErrorResponse(DmdataGenericResponse):
    status: str = Field("error")
    error: DmdataErrorModel


class DmdataStatusModel(BaseModel):
    status: str
    active_socket_id: Optional[str] = None
    websocket_errored: bool
    last_pong_time: int
    pong_time_delta: int
