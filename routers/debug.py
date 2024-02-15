import base64
import datetime
import gzip
import json
import os
from os.path import join, isfile

import xmltodict
from fastapi import APIRouter
from loguru import logger
from starlette.responses import JSONResponse

from env import Env
from internal.debug import debug_manager
from schemas.dmdata.generic import DmdataMessageTypes
from schemas.dmdata.socket import DmdataSocketData, DmdataSocketDataHead
from schemas.eew import EEWReturnModel
from schemas.jma.generic import JMAReportBaseModel
from schemas.p2p_info import EarthquakeIssueTypeEnum
from schemas.router import GenericResponseModel
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

tsunami_watch_files = [f
                       for f in os.listdir(relpath("../test/assets/tsunami_watch"))
                       if isfile(join(relpath("../test/assets/tsunami_watch"), f))]

tsunami_expectation_files = [f
                             for f in os.listdir(relpath("../test/assets/tsunami_expectation"))
                             if isfile(join(relpath("../test/assets/tsunami_expectation"), f))]

raw_files = [f
             for f in os.listdir(relpath("../test/assets/raw_messages"))
             if isfile(join(relpath("../test/assets/raw_messages"), f)) and f[0] != "."]

raw_files.sort()
forecast_files.sort()
warning_files.sort()
tsunami_watch_files.sort()
tsunami_expectation_files.sort()

forecast_index = 0
warning_index = 0
watch_index = 0
expectation_index = 0
raw_file_index = 0


@debug_router.get("/dmdata/forecast/list")
async def get_forecast_list():
    """
    Gets DMData forecast testing file list.
    """
    return forecast_files


@debug_router.get("/dmdata/warning/list")
async def get_warning_list():
    """
    Gets DMData warning testing file list.
    """
    return warning_files


@debug_router.get("/dmdata/tsunami_expectation/list")
async def get_tsunami_expectation_list():
    """
    Gets DMData tsunami expectation testing file list.
    """
    return tsunami_expectation_files


@debug_router.get("/dmdata/tsunami_watch/list")
async def get_tsunami_watch_list():
    """
    Gets DMData tsunami watch testing file list.
    """
    return tsunami_watch_files


@debug_router.get("/dmdata/{parse_type}/manual/{id}")
async def init_data(id: str, parse_type: str):
    """
    Initializes dmdata parsing.
    :param parse_type: Forecast or warning
    :param id: Id returned from list
    """
    if id not in forecast_files and id not in warning_files and \
            id not in tsunami_watch_files and id not in tsunami_expectation_files:
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
    elif parse_type == "warning":
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
    elif parse_type == "tsunami_expectation":
        if id not in tsunami_expectation_files:
            error = GenericResponseModel.BadRequest.value
            error["data"] = "ID not found"
            return JSONResponse(
                status_code=400,
                content=error
            )
        mocked_dmdata_socket.head.type = DmdataMessageTypes.tsunami_warning
        with open(join(base_path, "tsunami_expectation", id), encoding="utf-8") as f:
            content = f.read()
            f.close()
    elif parse_type == "tsunami_watch":
        if id not in tsunami_watch_files:
            error = GenericResponseModel.BadRequest.value
            error["data"] = "ID not found"
            return JSONResponse(
                status_code=400,
                content=error
            )
        mocked_dmdata_socket.head.type = DmdataMessageTypes.tsunami_info
        with open(join(base_path, "tsunami_watch", id), encoding="utf-8") as f:
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


async def init_file(file: str):
    mocked_dmdata_socket.head.type = None
    for i in DmdataMessageTypes:
        if i.value in file:
            mocked_dmdata_socket.head.type = i
    if mocked_dmdata_socket.head.type is None:
        logger.error(f"Unidentified raw file: {file}")
        return
    with open(join(base_path, "raw_messages", file), encoding="utf-8") as f:
        content = json.loads(f.read())
        f.close()
    message = base64.b64encode(gzip.compress(xmltodict.unparse(content).encode("utf-8"))).decode(encoding="utf-8")
    mocked_dmdata_socket.body = message
    mocked_dmdata_socket.xmlReport = JMAReportBaseModel.model_validate(content["Report"])
    Env.dmdata_instance.parse_data_message(mocked_dmdata_socket)


@debug_router.get("/dmdata/forecast/cycle")
async def cycle_forecast():
    """
    Cycles forecast.
    """
    global forecast_index
    current_file = forecast_files[forecast_index]
    await clear_eew()
    await init_data(current_file, "forecast")
    forecast_index += 1
    if forecast_index + 1 > len(forecast_files):
        forecast_index = 0

    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_forecast": current_file
        }
    )


@debug_router.get("/dmdata/warning/cycle")
async def cycle_warning():
    """
    Cycles warning.
    """
    global warning_index
    current_file = warning_files[warning_index]
    await clear_eew()
    await init_data(current_file, "warning")
    warning_index += 1
    if warning_index + 1 > len(warning_files):
        warning_index = 0

    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_forecast": current_file
        }
    )


@debug_router.get("/dmdata/tsunami_expectation/cycle")
async def cycle_tsunami_expectation():
    """
    Cycles tsunami expectation.
    """
    global expectation_index
    current_file = tsunami_expectation_files[expectation_index]
    await clear_eew()
    await init_data(current_file, "tsunami_expectation")
    expectation_index += 1
    if expectation_index + 1 > len(tsunami_expectation_files):
        expectation_index = 0

    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_forecast": current_file
        }
    )


@debug_router.get("/dmdata/tsunami_watch/cycle")
async def cycle_tsunami_watch():
    """
    Cycles tsunami watch.
    """
    global watch_index
    current_file = tsunami_watch_files[watch_index]
    await clear_eew()
    await init_data(current_file, "tsunami_watch")
    watch_index += 1
    if watch_index + 1 > len(tsunami_watch_files):
        watch_index = 0

    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_forecast": current_file
        }
    )


@debug_router.get("/dmdata/file/cycle")
async def cycle_file():
    """
    Cycles file.
    """
    global raw_file_index
    current_file = raw_files[raw_file_index]
    await clear_eew()
    await init_file(current_file)
    raw_file_index += 1
    if raw_file_index + 1 > len(raw_files):
        raw_file_index = 0

    return JSONResponse(
        status_code=200,
        content={
            "status": 0,
            "current_file": current_file
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


@debug_router.get("/dmdata/start_cycle")
def start_cycle(task: str, seconds: float = 2):
    """Starts refreshing cycle."""
    debug_manager.change_secs(seconds)
    if task == "forecast":
        task = cycle_forecast
    elif task == "warning":
        task = cycle_warning
    elif task == "tsunami_expectation":
        task = cycle_tsunami_expectation
    elif task == "tsunami_watch":
        task = cycle_tsunami_watch
    elif task == "file":
        task = cycle_file
    debug_manager.change_tasks([task])


@debug_router.get("/dmdata/end_cycle")
def end_cycle():
    """Ends refreshing cycle."""
    debug_manager.change_tasks([])
