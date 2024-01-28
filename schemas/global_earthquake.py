from pydantic import ConfigDict, BaseModel, Field


class CEICApiModel(BaseModel):
    id: int
    category_id: str = Field(validation_alias="CATA_ID")
    save_time: str = Field(validation_alias="SAVE_TIME")
    o_time: str = Field(validation_alias="O_TIME")
    latitude: str = Field(validation_alias="EPI_LAT")
    longitude: str = Field(validation_alias="EPI_LON")
    depth: int = Field(validation_alias="EPI_DEPTH")
    is_auto: str = Field(validation_alias="AUTO_FLAG")
    eq_type: str = Field(validation_alias="EQ_TYPE")
    o_time_fra: int = Field(validation_alias="O_TIME_FRA")
    m: str = Field(validation_alias="M")
    m_ms: int = Field(validation_alias="M_MS")
    m_ms7: int = Field(validation_alias="M_MS7")
    m_ml: int = Field(validation_alias="M_ML")
    m_mb: int = Field(validation_alias="M_MB")
    m_mb2: int = Field(validation_alias="M_MB2")
    sum_stn: int = Field(validation_alias="SUM_STN")
    loc_stn: int = Field(validation_alias="LOC_STN")
    location_c: str = Field(validation_alias="LOCATION_C")
    location_s: str = Field(validation_alias="LOCATION_S")
    category_type: str = Field(validation_alias="CATA_TYPE")
    sync_time: str = Field(validation_alias="SYNC_TIME")
    is_del: str = Field(validation_alias="IS_DEL")
    eq_category: str = Field(validation_alias="EQ_CATA_TYPE")
    t: int
    model_config = ConfigDict(populate_by_name=True)


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
