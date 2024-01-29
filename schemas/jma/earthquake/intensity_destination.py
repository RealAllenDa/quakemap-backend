from typing import Optional

from pydantic import BaseModel, Field

from schemas.jma.earthquake.generic import JMAIntensityEnum, JMAEqCommentModel
from schemas.jma.generic import JMAReportBaseModel
from schemas.jma.tsunami_expectation import JMAEarthquakeModel


class JMADetailIntStationModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    intensity: Optional[JMAIntensityEnum] = Field(None, validation_alias="Int")
    # Revise omitted


class JMADetailIntCityModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    max_intensity: Optional[JMAIntensityEnum] = Field(None, validation_alias="MaxInt")
    condition: Optional[str] = Field(None, validation_alias="Condition")
    # Revise omitted
    intensity_stations: JMADetailIntStationModel | list[JMADetailIntStationModel] \
        = Field(validation_alias="IntensityStation")


class JMADetailIntAreaModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    max_intensity: Optional[JMAIntensityEnum] = Field(None, validation_alias="MaxInt")
    # Revise omitted
    city: JMADetailIntCityModel | list[JMADetailIntCityModel] = Field(validation_alias="City")


class JMADetailIntPrefModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    max_intensity: Optional[JMAIntensityEnum] = Field(None, validation_alias="MaxInt")
    # Revise omitted
    area: JMADetailIntAreaModel | list[JMADetailIntAreaModel] = Field(validation_alias="Area")


class JMADetailIntObsModel(BaseModel):
    # CodeDefine omitted
    max_intensity: JMAIntensityEnum = Field(validation_alias="MaxInt")
    pref: JMADetailIntPrefModel | list[JMADetailIntPrefModel] = Field(validation_alias="Pref")


class JMADetailIntModel(BaseModel):
    observation: JMADetailIntObsModel = Field(validation_alias="Observation")


class JMAIntDestBody(BaseModel):
    earthquake: Optional[JMAEarthquakeModel] = Field(None, validation_alias="Earthquake")
    intensity: Optional[JMADetailIntModel] = Field(None, validation_alias="Intensity")
    text: Optional[str] = Field(None, validation_alias="Text")
    comments: Optional[JMAEqCommentModel] = Field(None, validation_alias="Comments")


class JMAIntDestModel(JMAReportBaseModel):
    body: JMAIntDestBody = Field(validation_alias="Body")
