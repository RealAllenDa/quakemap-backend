import base64
import datetime
import gzip
import os
from os.path import join, isfile

from fastapi import APIRouter
from starlette.responses import JSONResponse

from env import Env
from model.dmdata.generic import DmdataMessageTypes
from model.dmdata.socket import DmdataSocketData, DmdataSocketDataHead
from model.eew import EEWReturnModel
from model.p2p_info import EarthquakeIssueTypeEnum
from model.router import GenericResponseModel
from sdk import relpath

debug_router = APIRouter(
    prefix="/debug",
    tags=["debug"]
)
base_path = relpath("../test/assets")

mocked_dmdata_socket = DmdataSocketData(
    version="1.0",
    id="TESTING",
    classification="TESTING",
    passing=[],
    head=DmdataSocketDataHead(type=DmdataMessageTypes.eew_forecast, author="TEST", time=datetime.datetime.now(),
                              test=False, xml=True),
    format="xml",
    compression="gzip",
    encoding="base64",
    body=""
)
forecast_files = [f
                  for f in os.listdir(relpath("../test/assets/eew_forecast"))
                  if isfile(join(relpath("../test/assets/eew_forecast"), f))]

warning_files = [f
                 for f in os.listdir(relpath("../test/assets/eew_warning"))
                 if isfile(join(relpath("../test/assets/eew_warning"), f))]

forecast_index = 0
warning_index = 0


@debug_router.get("/dmdata/forecast/list")
async def get_forecast_list():
    """
    Gets DMData forecast testing file list.
    :return: DMData testing file list
    """
    return forecast_files


@debug_router.get("/dmdata/warning/list")
async def get_warning_list():
    """
    Gets DMData warning testing file list.
    :return: DMData warning file list
    """
    return warning_files


@debug_router.get("/dmdata/{parse_type}/manual/{id}")
async def init_data(id: str, parse_type: str):
    """
    Initializes dmdata parsing.
    :param parse_type: Forecast or warning
    :param id: Id returned from list
    """
    if id not in forecast_files and id not in warning_files:
        error = GenericResponseModel.BadRequest.value
        error["data"] = "ID not found"
        return JSONResponse(
            status_code=400,
            content=error
        )
    if parse_type == "forecast":
        if id not in forecast_files:
            error = GenericResponseModel.BadRequest.value
            error["data"] = "ID not found"
            return JSONResponse(
                status_code=400,
                content=error
            )
        mocked_dmdata_socket.head.type = DmdataMessageTypes.eew_forecast
        with open(join(base_path, "eew_forecast", id), encoding="utf-8") as f:
            content = f.read()
            f.close()
    else:
        if id not in warning_files:
            error = GenericResponseModel.BadRequest.value
            error["data"] = "ID not found"
            return JSONResponse(
                status_code=400,
                content=error
            )
        mocked_dmdata_socket.head.type = DmdataMessageTypes.eew_warning
        with open(join(base_path, "eew_warning", id), encoding="utf-8") as f:
            content = f.read()
            f.close()
    message = base64.b64encode(gzip.compress(content.encode(encoding="utf-8"))).decode(encoding="utf-8")
    mocked_dmdata_socket.body = message
    Env.dmdata_instance.parse_data_message(mocked_dmdata_socket)
    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_file": id
        }
    )


@debug_router.get("/dmdata/forecast/cycle")
async def cycle_forecast():
    """
    Cycles forecast.
    """
    global forecast_index
    await clear_eew()
    await init_data(forecast_files[forecast_index], "forecast")
    forecast_index += 1
    if forecast_index + 1 > len(forecast_files):
        forecast_index = 0

    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_forecast": forecast_files[forecast_index]
        }
    )


@debug_router.get("/dmdata/warning/cycle")
async def cycle_warning():
    """
    Cycles warning.
    """
    global warning_index
    await clear_eew()
    await init_data(warning_files[warning_index], "warning")
    warning_index += 1
    if warning_index + 1 > len(warning_files):
        warning_index = 0

    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_forecast": warning_files[warning_index]
        }
    )


@debug_router.get("/eew/clear")
async def clear_eew():
    """
    Clears EEW info.
    """
    from internal.modules_init import module_manager
    module_manager.classes["eew_info"].info = EEWReturnModel()

    return JSONResponse(
        status_code=200,
        content=GenericResponseModel.OK.value
    )


@debug_router.get("/p2p/{info_type}")
async def set_p2p_message(info_type: EarthquakeIssueTypeEnum):
    """
    Sets P2P message type.
    :param info_type: P2P Message Type
    """
    from internal.modules_init import module_manager
    Env.config.debug.p2p_info.enabled = True
    Env.config.debug.p2p_info.file = relpath(f"../test/assets/p2p/{info_type.value}.json")
    module_manager.classes["p2p_info"].get_info()
    return JSONResponse(
        status_code=200,
        content=GenericResponseModel.OK.value
    )
