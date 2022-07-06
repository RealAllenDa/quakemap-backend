__all__ = ["GlobalEarthquakeApiModel", "StatusCodeModel",
           "GENERIC_STATUS", "GenericResponseModel"]

from enum import Enum

from pydantic import BaseModel

from model.global_earthquake import GlobalEarthquakeReturnModel


class GenericResponseModel(dict, Enum):
    NotReady = {
        "status": -1,
        "data": "API not yet ready"
    }


class GlobalEarthquakeApiModel(BaseModel):
    status: int
    data: list[GlobalEarthquakeReturnModel]


class StatusCodeModel(BaseModel):
    status: int = -1
    data: str


GENERIC_STATUS = {
    404: {
        "model": StatusCodeModel
    }
}
