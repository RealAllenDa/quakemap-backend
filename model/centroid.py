from typing import Dict, Optional, List

from pydantic import ConfigDict, BaseModel, Field

__all__ = [
    "LatLngModel", "CentroidModel",
    "LatLngModelWithRegion", "CentroidModelWithRegion",
    "ObsStationsCentroidModel",
    "AreaToPositionCentroidModel", "AreaToPositionModel"
]


class LatLngModel(BaseModel):
    latitude: str
    longitude: str


class LatLngModelWithRegion(LatLngModel):
    region_code: str
    region_name: str


class LatLngModelUppercase(BaseModel):
    latitude: str = Field(validation_alias="Latitude")
    longitude: str = Field(validation_alias="Longitude")
    model_config = ConfigDict(populate_by_name=True)


class CentroidModel(BaseModel):
    content: Dict[str, LatLngModel] = {}


class CentroidModelWithRegion(BaseModel):
    content: Dict[str, LatLngModelWithRegion] = {}


class ObsStationPointModel(BaseModel):
    X: str
    Y: str


class ObsStationsCentroidModel(BaseModel):
    type: str = Field(validation_alias="Type")
    name: str = Field(validation_alias="Name")
    region: str = Field(validation_alias="Region")
    sub_region_code: str = Field(validation_alias="SubRegionCode")
    region_code: str = Field(validation_alias="RegionCode")
    is_suspended: bool = Field(validation_alias="IsSuspended")
    location: LatLngModelUppercase = Field(validation_alias="Location")
    old_location: Optional[LatLngModelUppercase] = Field(None, validation_alias="OldLocation")
    point: Optional[ObsStationPointModel] = Field(None, validation_alias="Point")
    # All null, so unused at all.
    classification_id: Optional[str] = Field(None, validation_alias="ClassificationId")
    prefecture_classification_id: Optional[str] = Field(None, validation_alias="PrefectureClassificationId")
    model_config = ConfigDict(populate_by_name=True)


class AreaToPositionModel(BaseModel):
    name: str
    position: List[str]


class AreaToPositionCentroidModel(BaseModel):
    content: Dict[str, AreaToPositionModel] = {}
