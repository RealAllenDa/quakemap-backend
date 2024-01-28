from pydantic import BaseModel


class TimeSyncModel(BaseModel):
    server_timestamp: int
    difference: int
