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

# --- Internals initialization
Env.geojson_instance = GeoJson()
Env.centroid_instance = Centroid()
Env.intensity2color_instance = IntensityToColor()
Env.pswave_instance = PSWave()
module_manager.init()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=Env.config.server.host,
        port=int(Env.config.server.port)
    )
