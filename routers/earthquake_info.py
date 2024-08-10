from fastapi import APIRouter
from starlette.responses import PlainTextResponse

from env import Env
from internal.modules_init import module_manager
from modules.eew_info.middleware import EEWInfoMiddleWare
from schemas.p2p_info import EarthquakeInfoReturnModel
from schemas.router import GENERIC_STATUS

earthquake_router = APIRouter(
    prefix="/api",
    tags=["earthquake"]
)


@earthquake_router.get("/earthquake_info",
                       response_model=EarthquakeInfoReturnModel,
                       tags=["earthquake"],
                       responses=GENERIC_STATUS)
async def get_p2p_info():
    """
    Gets earthquake info from P2P and EEW.
    :return:
        - Status code 200 when OK
        - Status code 404 when API is not ready
    """
    p2p_info = module_manager.get_module_info("p2p_info")
    eew_info = module_manager.get_module_info("eew_info")
    return EarthquakeInfoReturnModel(
        info=p2p_info.earthquake,
        eew=EEWInfoMiddleWare.use_svir_or_kmoni(eew_info)
    )


@earthquake_router.get("/raw_data",
                       response_class=PlainTextResponse,
                       tags=["earthquake"])
def get_raw_data():
    """
    Gets raw earthquake data.
    """
    return Env.dmdata_instance.message
