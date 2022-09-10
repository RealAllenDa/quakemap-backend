#  CONFIDENTIAL HomeNetwork
#  Unpublished Copyright (c) 2022.
#
#  NOTICE: All information contained herein is, and remains the property of HomeNetwork.
#  Dissemination of this information or reproduction of this material is strictly forbidden unless
#  prior written permission is obtained from HomeNetwork.
from pydantic import BaseModel, Field


class DmdataGenericErrorModel(BaseModel):
    error: str
    error_description: str


class DmdataGenericResponse(BaseModel):
    response_id: str
    response_time: str
    status: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "response_id": "responseId",
            "response_time": "responseTime",
            "status": "status"
        }


class DmdataErrorModel(BaseModel):
    message: str
    code: int


class DmdataGenericErrorResponse(DmdataGenericResponse):
    status: str = Field("error")
    error: DmdataErrorModel