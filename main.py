import logging
import os.path
import sys

import requests
import sentry_sdk
import urllib3
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from loguru import logger
from sentry_sdk.integrations.logging import BreadcrumbHandler, EventHandler, LoggingIntegration
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from urllib3.exceptions import InsecureRequestWarning

import config
from env import Env
from internal.centroid import Centroid
from internal.db import Database
from internal.dmdata import DMDataFetcher
from internal.geojson import GeoJson
from internal.intensity2color import IntensityToColor
from internal.modules_init import module_manager
from internal.pswave import PSWave
from routers import global_earthquake_router, earthquake_router, shake_level_router, tsunami_router, debug_router, \
    heartbeat_router, index_router
from schemas.config import RunEnvironment
from schemas.router import GenericResponseModel
from sdk import relpath

# --- Constants
RUN_ENV = RunEnvironment(os.getenv("ENV")) \
    if os.getenv("ENV") \
    else RunEnvironment.development
load_dotenv(f".{RUN_ENV.value}.env")

# --- Config initialization
config.init_config(RUN_ENV)
Env.run_env = RUN_ENV

# --- Error tracking initialization
if Env.config.sentry.enabled:
    if os.getenv("SENTRY_URL"):
        logger.debug(f"SENTRY_URL={os.getenv('SENTRY_URL')}. sample_rate={Env.config.sentry.sample_rate}. "
                     f"release={Env.version}")
        _ = logger.add(
            BreadcrumbHandler(level=logging.DEBUG),
            diagnose=Env.config.logger.diagnose,
            level=logging.DEBUG,
        )
        _ = logger.add(
            EventHandler(level=logging.ERROR),
            diagnose=Env.config.logger.diagnose,
            level=logging.ERROR,
        )
        integrations = [
            LoggingIntegration(level=None, event_level=None),
        ]

        sentry_sdk.init(
            dsn=os.getenv("SENTRY_URL"),
            traces_sample_rate=Env.config.sentry.sample_rate.traces,
            sample_rate=Env.config.sentry.sample_rate.errors,
            integrations=integrations,
            environment=RUN_ENV.value,
            release=f"quakemap-back@{Env.version}"
        )
        logger.success("Initialized sentry.")
    else:
        logger.critical("Failed to initialize sentry: "
                        "No SENTRY_URL defined in environment.")
        sys.exit(1)

# --- Runtime initialization
urllib3.disable_warnings(InsecureRequestWarning)
# Force IPV4: currently no ipv6 allowed
# noinspection PyUnresolvedReferences
requests.packages.urllib3.util.connection.HAS_IPV6 = False

app = FastAPI(
    docs_url="/docs" if Env.config.utilities.doc else None,
    redoc_url="/redoc" if Env.config.utilities.redoc else None
)

app.mount("/static", StaticFiles(directory=relpath("static")), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, __):
    return JSONResponse(status_code=500,
                        content=GenericResponseModel.ServerError.value)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 404:
        return JSONResponse(status_code=404,
                            content=GenericResponseModel.NotFound.value)
    else:
        return await http_exception_handler(request, exc)


# --- Router initialization
app.include_router(global_earthquake_router)
app.include_router(earthquake_router)
app.include_router(shake_level_router)
app.include_router(tsunami_router)
if Env.run_env == RunEnvironment.testing:
    app.include_router(debug_router)
app.include_router(heartbeat_router)
app.include_router(index_router)

# --- Middleware initialization
if Env.config.utilities.cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.success("Added CORS middleware.")
app.add_middleware(GZipMiddleware)
logger.success("Added gzip middleware.")


@app.on_event("shutdown")
async def shutdown_wrapper():
    module_manager.stop_program()


# --- Internals initialization
Env.geojson_instance = GeoJson()
Env.centroid_instance = Centroid()
Env.intensity2color_instance = IntensityToColor()
Env.pswave_instance = PSWave()
if Env.config.dmdata.enabled:
    Env.dmdata_instance = DMDataFetcher()
Env.db_instance = Database()
module_manager.init()

if __name__ == "__main__":
    # noinspection PyTypeChecker
    uvicorn.run(
        app,
        host=Env.config.server.host,
        port=int(Env.config.server.port)
    )
