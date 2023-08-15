from enum import Enum

from pydantic import BaseModel

from schemas.dmdata.generic import DmdataGenericErrorModel


class DmdataRequestTokenBodyModel(BaseModel):
    client_id: str
    client_secret: str
    grant_type: str = "refresh_token"
    refresh_token: str


class DmdataRefreshTokenResponseModel(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: str


class DmdataRefreshTokenErrors(str, Enum):
    invalid_request = "invalid_request"
    invalid_client = "invalid_client"
    invalid_grant = "invalid_grant"
    unauthorized_client = "unauthorized_client"
    unsupported_grant_type = "unsupported_grant_type"
    server_error = "server_error"


class DmdataRefreshTokenErrorModel(DmdataGenericErrorModel):
    error: DmdataRefreshTokenErrors
