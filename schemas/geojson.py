__all__ = ["GeoJsonModel", "TsunamiGeoJsonModel"]

from typing import List, Optional

from pydantic import BaseModel


class _GeoJsonGeometry(BaseModel):
    type: str
    # No further definitions, since manipulating GeoJson
    # is not needed in this program.
    coordinates: list


class _GeoJsonProperties(BaseModel):
    code: str
    name: str
    namekana: str


class _TsunamiGeoJsonProperties(_GeoJsonProperties):
    grade: Optional[str] = "Unknown"
    intensity_color: Optional[str] = ""


class _GeoJsonFeatures(BaseModel):
    type: str
    geometry: Optional[_GeoJsonGeometry] = None
    properties: _GeoJsonProperties


class _TsunamiGeoJsonFeatures(_GeoJsonFeatures):
    properties: _TsunamiGeoJsonProperties


class GeoJsonModel(BaseModel):
    type: str = "FeatureCollection"
    features: List[_GeoJsonFeatures] = []


class TsunamiGeoJsonModel(GeoJsonModel):
    features: List[_TsunamiGeoJsonFeatures] = []
