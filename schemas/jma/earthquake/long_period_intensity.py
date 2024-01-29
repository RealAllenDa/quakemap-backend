from typing import Optional

from pydantic import Field, BaseModel

from schemas.jma.earthquake.generic import JMALgIntensityEnum, JMAIntensityEnum, JMAEqCommentModel
from schemas.jma.earthquake.intensity_destination import JMADetailIntObsModel, JMADetailIntPrefModel, \
    JMADetailIntStationModel
from schemas.jma.generic import JMAReportBaseModel
from schemas.jma.tsunami_expectation import JMAEarthquakeModel


class JMADetailLgIntStationModel(JMADetailIntStationModel):
    lg_intensity: Optional[JMALgIntensityEnum] = Field(None, validation_alias="LgInt")
    # Revise, Sva, SvaPerPeriod, LgIntPerPeriod omitted


class JMADetailLgIntAreaModel(BaseModel):
    name: str = Field(validation_alias="Name")
    code: str = Field(validation_alias="Code")
    max_intensity: Optional[JMAIntensityEnum] = Field(None, validation_alias="MaxInt")
    max_lg_intensity: Optional[JMALgIntensityEnum] = Field(None, validation_alias="MaxLgInt")
    # Revise omitted
    city: JMADetailLgIntStationModel | list[JMADetailLgIntStationModel] = Field(validation_alias="IntensityStation")


class JMADetailLgIntPrefModel(JMADetailIntPrefModel):
    max_lg_intensity: Optional[JMALgIntensityEnum] = Field(None, validation_alias="MaxLgInt")
    # Revise omitted
    area: JMADetailLgIntAreaModel | list[JMADetailLgIntAreaModel] = Field(validation_alias="Area")


class JMADetailLgIntObsModel(JMADetailIntObsModel):
    # CodeDefine omitted
    max_lg_intensity: JMALgIntensityEnum = Field(validation_alias="MaxLgInt")
    # LgCategory omitted
    pref: JMADetailLgIntPrefModel | list[JMADetailLgIntPrefModel] = Field(validation_alias="Pref")


class JMADetailLgIntModel(BaseModel):
    observation: JMADetailLgIntObsModel = Field(validation_alias="Observation")


class JMALongPeriodIntBody(BaseModel):
    earthquake: Optional[JMAEarthquakeModel] = Field(None, validation_alias="Earthquake")
    intensity: Optional[JMADetailLgIntModel] = Field(None, validation_alias="Intensity")
    text: Optional[str] = Field(None, validation_alias="Text")
    comments: Optional[JMAEqCommentModel] = Field(None, validation_alias="Comments")
    # URI omitted


class JMALongPeriodIntModel(JMAReportBaseModel):
    body: JMALongPeriodIntBody = Field(validation_alias="Body")
