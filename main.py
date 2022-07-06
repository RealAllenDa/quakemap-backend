import os.path

import urllib3
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from urllib3.exceptions import InsecureRequestWarning

import config
from env import Env
from internal.centroid import Centroid
from internal.geojson import GeoJson
from internal.intensity2color import IntensityToColor
from internal.modules_init import module_manager
from internal.pswave import PSWave
from model.config import RunEnvironment
from routers import global_earthquake_router, earthquake_router, shake_level_router

# --- Constants
VERSION = "0.0.1 Indev"
RUN_ENV = RunEnvironment(os.getenv("ENV")) \
    if os.getenv("ENV") \
    else RunEnvironment.development

# --- Runtime initialization
urllib3.disable_warnings(InsecureRequestWarning)
app = FastAPI()

# --- Config initialization
config.init_config(RUN_ENV)

# --- Router initialization
app.include_router(global_earthquake_router)
app.include_router(earthquake_router)
app.include_router(shake_level_router)

# --- Middleware initialization
if Env.config.utilities.cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.success("Added CORS middleware.")

# --- Internals initialization
Env.geojson_instance = GeoJson()
Env.centroid_instance = Centroid()
Env.intensity2color_instance = IntensityToColor()
Env.pswave_instance = PSWave()
module_manager.init()
