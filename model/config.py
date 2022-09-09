from enum import Enum

from pydantic import BaseModel

__all__ = ["ConfigModel", "RunEnvironment", "LogLevelEnum", "ProxyConfigModel",
           "EEWTargetEnum"]


class ProxyConfigModel(BaseModel):
    http: str
    https: str


class ModulesEnableModel(BaseModel):
    eew: bool
    tsunami: bool
    p2p_earthquake: bool
    shake_level: bool
    global_earthquake: bool


class UtilitiesEnableModel(BaseModel):
    update_centroid: bool
    cors: bool
    doc: bool
    redoc: bool


class EEWTargetEnum(str, Enum):
    svir = "svir"
    iedred = "iedred"


class EEWConfigModel(BaseModel):
    target: EEWTargetEnum


class _GenericDebugModel(BaseModel):
    enabled: bool


class _FileDebugModel(_GenericDebugModel):
    file: str


class _SVIRDebugModel(_FileDebugModel):
    ignore_outdated: bool


class _KmoniDebugModel(_GenericDebugModel):
    start_time: str
    image_override: _FileDebugModel


class DebugConfigModel(BaseModel):
    global_earthquake: _GenericDebugModel
    tsunami_watch: _FileDebugModel
    p2p_info: _FileDebugModel
    tsunami: _FileDebugModel
    iedred_eew: _FileDebugModel
    svir_eew: _SVIRDebugModel
    kmoni_eew: _KmoniDebugModel
    shake_level: _GenericDebugModel


class LogLevelEnum(str, Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class _TsunamiColorModel(BaseModel):
    MajorWarning: str
    Warning: str
    Watch: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            "MajorWarning": "major_warning",
            "Warning": "warning",
            "Watch": "watch"
        }


class TsunamiConfigModel(BaseModel):
    color: _TsunamiColorModel


class LoggerConfigModel(BaseModel):
    level: LogLevelEnum
    backtrace: bool
    diagnose: bool
    retention: str


class GlobalEarthquakeConfigModel(BaseModel):
    list_count: int


class ServerModel(BaseModel):
    host: str
    port: str


class DMDataConfigModel(BaseModel):
    enabled: bool
    client_id: str
    client_token: str


class ConfigModel(BaseModel):
    logger: LoggerConfigModel
    proxy: ProxyConfigModel
    modules: ModulesEnableModel
    utilities: UtilitiesEnableModel
    eew: EEWConfigModel
    tsunami: TsunamiConfigModel
    server: ServerModel
    dmdata: DMDataConfigModel
    debug: DebugConfigModel
    global_earthquake: GlobalEarthquakeConfigModel


class RunEnvironment(Enum):
    development = "development"
    production = "production"
