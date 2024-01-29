from typing import Optional

from pydantic import Field, BaseModel

from schemas.jma.generic import JMAReportBaseModel
from schemas.jma.tsunami_expectation import JMAEarthquakeModel


class JMAEpicenterUpdateBody(BaseModel):
    earthquake: Optional[JMAEarthquakeModel] = Field(None, validation_alias="Earthquake")
    text: Optional[str] = Field(None, validation_alias="Text")
    # Comments omitted


class JMAEpicenterUpdateModel(JMAReportBaseModel):
    body: JMAEpicenterUpdateBody = Field(validation_alias="Body")
