from pydantic import BaseModel

__all__ = ["TimeSyncModel"]


class TimeSyncModel(BaseModel):
    server_timestamp: int
    difference: int
