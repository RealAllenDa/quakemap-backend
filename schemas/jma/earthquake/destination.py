from typing import Optional

from pydantic import BaseModel, Field

from schemas.jma.earthquake.generic import JMAEqCommentModel
from schemas.jma.generic import JMAReportBaseModel
from schemas.jma.tsunami_expectation import JMAEarthquakeModel


class JMADestinationBody(BaseModel):
    earthquake: Optional[JMAEarthquakeModel] = Field(None, validation_alias="Earthquake")
    text: Optional[str] = Field(None, validation_alias="Text")
    comments: Optional[JMAEqCommentModel] = Field(None, validation_alias="Comments")


class JMADestinationModel(JMAReportBaseModel):
    body: JMADestinationBody = Field(validation_alias="Body")
