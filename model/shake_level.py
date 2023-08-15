__all__ = ["ShakeLevelReturnModel", "ShakeLevelApiModel"]

from typing import Optional

from pydantic import ConfigDict, BaseModel, Field


class ShakeLevelReturnModel(BaseModel):
    shake_level: int = Field(validation_alias="l")
    green: int = Field(validation_alias="g")
    yellow: int = Field(validation_alias="y")
    red: int = Field(validation_alias="r")
    sync_time: str = Field(validation_alias="t")
    status: Optional[int] = Field(None, validation_alias="e")
    model_config = ConfigDict(populate_by_name=True)


class ShakeLevelApiModel(BaseModel):
    shake_level: int
    green: int
    yellow: int
    red: int
    status: int
