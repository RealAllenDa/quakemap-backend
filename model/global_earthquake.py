from pydantic import BaseModel

__all__ = ["CEICApiModel", "EpicenterModel", "GlobalEarthquakeReturnModel",
           "GlobalEarthquakeApiModel"]


class CEICApiModel(BaseModel):
    id: int
    category_id: str
    save_time: str
    o_time: str
    latitude: str
    longitude: str
    depth: int
    is_auto: str
    eq_type: str
    o_time_fra: int
    m: str
    m_ms: int
    m_ms7: int
    m_ml: int
    m_mb: int
    m_mb2: int
    sum_stn: int
    loc_stn: int
    location_c: str
    location_s: str
    category_type: str
    sync_time: str
    is_del: str
    eq_category: str
    t: int

    class Config:
        allow_population_by_field_name = True
        fields = {
            "id": "id",
            "category_id": "CATA_ID",
            "save_time": "SAVE_TIME",
            "o_time": "O_TIME",
            "latitude": "EPI_LAT",
            "longitude": "EPI_LON",
            "depth": "EPI_DEPTH",
            "is_auto": "AUTO_FLAG",
            "eq_type": "EQ_TYPE",
            "o_time_fra": "O_TIME_FRA",
            "m": "M",
            "m_ms": "M_MS",
            "m_ms7": "M_MS7",
            "m_ml": "M_ML",
            "m_mb": "M_MB",
            "m_mb2": "M_MB2",
            "sum_stn": "SUM_STN",
            "loc_stn": "LOC_STN",
            "location_c": "LOCATION_C",
            "location_s": "LOCATION_S",
            "category_type": "CATA_TYPE",
            "sync_time": "SYNC_TIME",
            "is_del": "IS_DEL",
            "eq_category": "EQ_CATA_TYPE",
            "t": "t"
        }


class EpicenterModel(BaseModel):
    name: str
    depth: str
    latitude: float
    longitude: float


class GlobalEarthquakeReturnModel(BaseModel):
    epicenter: EpicenterModel
    magnitude: str
    mmi: int
    occur_time: str
    receive_time: str


class GlobalEarthquakeApiModel(BaseModel):
    status: int
    data: list[GlobalEarthquakeReturnModel]
