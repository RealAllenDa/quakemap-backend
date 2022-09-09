from fastapi import APIRouter
from starlette.responses import JSONResponse

from internal.modules_init import module_manager
from model.global_earthquake import GlobalEarthquakeApiModel
from model.router import GENERIC_STATUS, GenericResponseModel

__all__ = ["global_earthquake_router"]

global_earthquake_router = APIRouter(
    prefix="/api",
    tags=["global_earthquake"]
)


@global_earthquake_router.get("/global_earthquake_info",
                              response_model=GlobalEarthquakeApiModel,
                              tags=["global_earthquake"],
                              responses=GENERIC_STATUS)
async def get_global_earthquake_info():
    """
    Gets global earthquake info from the module.
    :return:
        - Status code 200 when OK
        - Status code 404 when API is not ready
    """
    if module_manager.get_module_info("global_earthquake") is None:
        return JSONResponse(status_code=404,
                            content=GenericResponseModel.NotReady.value)
    return GlobalEarthquakeApiModel(
        status=0,
        data=module_manager.get_module_info("global_earthquake")
    )
