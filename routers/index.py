import time

from fastapi import APIRouter

__all__ = ["index_router"]

from starlette.responses import PlainTextResponse

from model.index import TimeSyncModel

index_router = APIRouter()


@index_router.get("/",
                  response_class=PlainTextResponse)
async def get_home():
    """
    Returns indicator that the server has started up.
    """
    return "It works!"


@index_router.get("/time",
                  response_model=TimeSyncModel)
async def get_server_time(ct: int) -> TimeSyncModel:
    """
    Synchronizes server time with client time.
    :param ct: The client time
    """
    server_timestamp = int(round(time.time() * 1000))
    difference = server_timestamp - ct
    return TimeSyncModel(
        server_timestamp=server_timestamp,
        difference=difference
    )
