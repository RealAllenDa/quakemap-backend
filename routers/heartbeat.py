from fastapi import APIRouter

__all__ = ["heartbeat_router"]

from schemas.dmdata.generic import DmdataStatusModel

heartbeat_router = APIRouter(
    tags=["heartbeat"]
)


@heartbeat_router.get("/heartbeat/dmdata",
                      response_model=DmdataStatusModel,
                      tags=["heartbeat"])
async def heartbeat_dmdata():
    """
    Checks dmdata status.
    """
    from env import Env
    return Env.dmdata_instance.status
