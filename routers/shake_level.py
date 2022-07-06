__all__ = ["shake_level_router"]

from fastapi import APIRouter
from starlette.responses import JSONResponse

from internal.modules_init import module_manager
from model.router import GENERIC_STATUS, GenericResponseModel
from model.shake_level import ShakeLevelApiModel

shake_level_router = APIRouter(
    prefix="/api",
    tags=["shake_level"]
)


@shake_level_router.get("/shake_level",
                        response_model=ShakeLevelApiModel,
                        tags=["shake_level"],
                        responses=GENERIC_STATUS)
async def get_shake_level_info():
    """
    Gets shake level info from the module.
    :return:
        - Status code 200 when OK
        - Status code 404 when API is not ready
    """
    info = module_manager.get_module_info("shake_level")
    if info is None:
        return JSONResponse(status_code=404,
                            content=GenericResponseModel.NotReady.value)
    return info
