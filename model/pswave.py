__all__ = ["TravelTimeTableModel", "PSWaveTimeModel"]

from typing import Optional

from pydantic import BaseModel


class TravelTimeTableModel(BaseModel):
    p_time: float
    s_time: float
    depth: int
    distance: int


class PSWaveTimeModel(BaseModel):
    p_time: Optional[float] = None
    s_time: Optional[float] = None
