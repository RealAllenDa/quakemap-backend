import os.path

import urllib3
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse
from urllib3.exceptions import InsecureRequestWarning

import config
from env import Env
from internal.centroid import Centroid
from internal.dmdata import DMDataFetcher
from internal.geojson import GeoJson
from internal.intensity2color import IntensityToColor
from internal.modules_init import module_manager
from internal.pswave import PSWave
from model.config import RunEnvironment
from model.router import GenericResponseModel
from routers import global_earthquake_router, earthquake_router, shake_level_router, tsunami_router

# --- Constants
VERSION = "0.0.1 Indev"
RUN_ENV = RunEnvironment(os.getenv("ENV")) \
    if os.getenv("ENV") \
    else RunEnvironment.development
load_dotenv(f".{RUN_ENV.value}.env")

# --- Config initialization
config.init_config(RUN_ENV)

# --- Runtime initialization
urllib3.disable_warnings(InsecureRequestWarning)
app = FastAPI(
    docs_url="/docs" if Env.config.utilities.doc else None,
    redoc_url="/redoc" if Env.config.utilities.redoc else None
)


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
module_manager.init()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=Env.config.server.host,
        port=int(Env.config.server.port)
    )
