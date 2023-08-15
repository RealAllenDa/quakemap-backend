__all__ = ["tsunami_router"]

from fastapi import APIRouter
from loguru import logger
from starlette.responses import PlainTextResponse

from internal.modules_init import module_manager
from schemas.router import GENERIC_STATUS
from schemas.tsunami import TsunamiTotalInfoModel

tsunami_router = APIRouter(
    prefix="/api",
    tags=["tsunami"]
)


def get_is_tsunami(in_effect: bool) -> str:
    """
    Returns 1 if tsunami warning is in effect.

    :param in_effect: Whether tsunami warning is in effect
    :return: 1 or 0
    """
    return "1" if in_effect else "0"


def get_tsunami_status() -> str:
    """
    Returns 1 if tsunami warning is in effect.

    :return: 1 or 0
    """
    info = module_manager.classes.get("tsunami")
    if info is not None:
        is_tsunami_jma = info.tsunami_warning_in_effect
    else:
        is_tsunami_jma = None

    p2p_info = module_manager.get_module_info("p2p_info")
    if p2p_info is not None:
        is_tsunami_p2p = "1" == p2p_info.tsunami_in_effect
    else:
        is_tsunami_p2p = None

    if info and p2p_info:
        if is_tsunami_p2p == is_tsunami_jma:
            return get_is_tsunami(is_tsunami_p2p)
        else:
            if is_tsunami_p2p is True:
                # P2P will ALWAYS issue warning BEFORE JMA!!!
                # If P2P has warning but JMA hasn't, maybe there's something wrong with JMA message parsing.
                logger.warning("Message discrepancy between JMA and P2P: Probably JMA error, choosing P2P")
                return get_is_tsunami(is_tsunami_p2p)
            else:
                # However, if P2P hasn't warning but JMA has, maybe P2P has a mistake.
                logger.warning("Message discrepancy between JMA and P2P: Probably P2P error, choosing JMA")
                return get_is_tsunami(is_tsunami_jma)
    elif (not info) and p2p_info:
        logger.warning("JMA info not avail: returning P2P")
        return get_is_tsunami(is_tsunami_p2p)
    elif info and (not p2p_info):
        logger.warning("P2P info not avail: returning JMA")
        return get_is_tsunami(is_tsunami_jma)
    else:
        logger.warning("All info not avail!")
        return "0"


@tsunami_router.get("/is_tsunami",
                    response_class=PlainTextResponse,
                    tags=["tsunami"],
                    responses=GENERIC_STATUS)
async def get_shake_level_info():
    """
    Check if the tsunami warning has been issued.
    :return:
        Issued=1, None=0
    """
    return get_tsunami_status()


@tsunami_router.get("/tsunami_info",
                    response_model=TsunamiTotalInfoModel,
                    tags=["tsunami"],
                    responses=GENERIC_STATUS)
async def get_shake_level_info():
    """
    Gets the tsunami info.
    :return:
        - Status code 200 when OK
        - Status code 404 when API is not ready
    """
    info = module_manager.classes.get("tsunami")
    if info is not None:
        is_tsunami_jma = get_is_tsunami(info.tsunami_watch_in_effect)
    else:
        is_tsunami_jma = "0"

    p2p_info = module_manager.get_module_info("p2p_info")
    if p2p_info is not None:
        map_info = p2p_info.tsunami
    else:
        map_info = None

    return TsunamiTotalInfoModel(
        status=get_tsunami_status(),
        status_forecast=is_tsunami_jma,
        map=map_info,
        info=info.tsunami_expectation_info,
        watch=info.tsunami_obs_info
    )
