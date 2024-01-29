from typing import Optional

from pydantic import BaseModel, Field

from schemas.jma.earthquake.generic import JMAEqCommentModel, JMAIntensityEnum
from schemas.jma.generic import JMAReportBaseModel


class JMAIntAreaModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    max_intensity: JMAIntensityEnum = Field(validation_alias="MaxInt")  # should be higher than 3


class JMAIntPrefModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    max_intensity: JMAIntensityEnum = Field(validation_alias="MaxInt")  # should be higher than 3
    area: list[JMAIntAreaModel] | JMAIntAreaModel = Field(validation_alias="Area")


class JMAIntObsModel(BaseModel):
    # CodeDefine omitted
    max_intensity: JMAIntensityEnum = Field(validation_alias="MaxInt")  # should be higher than 3
    pref: list[JMAIntPrefModel] | JMAIntPrefModel = Field(validation_alias="Pref")


class JMAIntModel(BaseModel):
    observation: JMAIntObsModel = Field(validation_alias="Observation")


class JMAIntReportBody(BaseModel):
    intensity: Optional[JMAIntModel] = Field(None, validation_alias="Intensity")
    text: Optional[str] = Field(None, validation_alias="Text")
    comments: Optional[JMAEqCommentModel] = Field(None, validation_alias="Comments")


class JMAIntReportModel(JMAReportBaseModel):
    body: JMAIntReportBody = Field(validation_alias="Body")
