__all__ = ["ShakeLevelReturnModel", "ShakeLevelApiModel"]

from pydantic import BaseModel


class ShakeLevelReturnModel(BaseModel):
    shake_level: int
    green: int
    yellow: int
    red: int
    sync_time: str
    status: int

    class Config:
        allow_population_by_field_name = True
        fields = {
            "shake_level": "l",
            "green": "g",
            "yellow": "y",
            "red": "r",
            "sync_time": "t",
            "status": "e"
        }


class ShakeLevelApiModel(BaseModel):
    shake_level: int
    green: int
    yellow: int
    red: int
    status: int
