from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel


class StationIntensityModel(BaseModel):
    name: str
    area_code: str
    sub_area_code: str
    latitude: str
    longitude: str
    intensity: str
    detail_intensity: float
    is_area: bool


class AreaIntensityModel(BaseModel):
    name: str
    intensity: str
    lg_intensity: Optional[Any] = None
    is_area: bool
    latitude: str
    longitude: str


class IntensityToColorIntEnum(int, Enum):
    one = 1
    two = 2
    three = 3
    four = 4
    five_lower = 5
    five_upper = 6
    six_lower = 7
    six_upper = 8
    seven = 9


class IntensityToColorReturnModel(BaseModel):
    station_intensities: dict[str, StationIntensityModel] = {}
    area_intensities: dict[str, AreaIntensityModel] = {}
    recommend_areas: bool = False
