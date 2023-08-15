__all__ = ["StatusCodeModel",
           "GENERIC_STATUS", "GenericResponseModel"]

from enum import Enum

from pydantic import BaseModel


class GenericResponseModel(dict, Enum):
    OK = {
        "status": 0,
        "data": "OK"
    }
    NotReady = {
        "status": -1,
        "data": "API not yet ready"
    }
    ServerError = {
        "status": -2,
        "data": "Internal server error"
    }
    NotFound = {
        "status": -4,
        "data": "Not found"
    }
    BadRequest = {
        "status": -5,
        "data": "Bad request"
    }


class StatusCodeModel(BaseModel):
    status: int = -1
    data: str


GENERIC_STATUS = {
    404: {
        "model": StatusCodeModel
    },
    500: {
        "model": StatusCodeModel
    },
}
