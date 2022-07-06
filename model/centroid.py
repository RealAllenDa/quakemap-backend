from typing import Dict, Optional, List

from pydantic import BaseModel

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
    latitude: str
    longitude: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "latitude": "Latitude",
            "longitude": "Longitude"
        }


class CentroidModel(BaseModel):
    content: Dict[str, LatLngModel] = {}


class CentroidModelWithRegion(BaseModel):
    content: Dict[str, LatLngModelWithRegion] = {}


class ObsStationPointModel(BaseModel):
    X: str
    Y: str


class ObsStationsCentroidModel(BaseModel):
    type: str
    name: str
    region: str
    sub_region_code: str
    region_code: str
    is_suspended: bool
    location: LatLngModelUppercase
    old_location: Optional[LatLngModelUppercase]
    point: Optional[ObsStationPointModel]
    # All null, so unused at all.
    classification_id: Optional[str]
    prefecture_classification_id: Optional[str]

    class Config:
        allow_population_by_field_name = True
        fields = {
            "type": "Type",
            "name": "Name",
            "region": "Region",
            "sub_region_code": "SubRegionCode",
            "region_code": "RegionCode",
            "is_suspended": "IsSuspended",
            "location": "Location",
            "old_location": "OldLocation",
            "point": "Point",
            "classification_id": "ClassificationId",
            "prefecture_classification_id": "PrefectureClassificationId"
        }


class AreaToPositionModel(BaseModel):
    name: str
    position: List[str]


class AreaToPositionCentroidModel(BaseModel):
    content: Dict[str, AreaToPositionModel] = {}
