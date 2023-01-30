from fastapi import APIRouter
from starlette.responses import PlainTextResponse

__all__ = ["heartbeat_router"]

from model.dmdata.generic import DmdataStatusModel

heartbeat_router = APIRouter(
    tags=["heartbeat"]
)


@heartbeat_router.get("/",
                      response_class=PlainTextResponse,
                      tags=["heartbeat"])
async def get_home():
    """
    Returns indicator that the server has started up.
    """
    return "It works!"


@heartbeat_router.get("/heartbeat/dmdata",
                      response_model=DmdataStatusModel,
                      tags=["heartbeat"])
async def heartbeat_dmdata():
    """
    Checks dmdata status.
    """
    from env import Env
    return Env.dmdata_instance.status
