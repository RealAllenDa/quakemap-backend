from internal.centroid import Centroid
from internal.geojson import GeoJson
from internal.intensity2color import IntensityToColor
from internal.pswave import PSWave
from model.config import ConfigModel

__all__ = ["Env"]

from sdk import verify_none, verify_type, verify_not_used


class _Env:
    """
    Shared variables across project.
    """

    def __init__(self) -> None:
        self._init_time = None
        self._config = None
        self._geojson_instance = None
        self._centroid_instance = None
        self._intensity_to_color_instance = None
        self._pswave_instance = None
        self._module_manager = None

    @property
    def init_time(self) -> int:
        verify_none(self._init_time)
        return self._init_time

    # noinspection PyUnusedLocal
    @init_time.setter
    def init_time(self, value: int) -> None:
        if self._init_time is not None:
            verify_not_used("init_time", "repetitively set")
        verify_type(value, int)
        self._init_time = value

    @property
    def config(self) -> ConfigModel:
        verify_none(self._config)
        return self._config

    @config.setter
    def config(self, config: ConfigModel) -> None:
        verify_type(config, ConfigModel)
        self._config = config

    @property
    def geojson_instance(self) -> GeoJson:
        verify_none(self._geojson_instance)
        return self._geojson_instance

    @geojson_instance.setter
    def geojson_instance(self, instance: GeoJson) -> None:
        verify_type(instance, GeoJson)
        self._geojson_instance = instance

    @property
    def centroid_instance(self) -> Centroid:
        verify_none(self._centroid_instance)
        return self._centroid_instance

    @centroid_instance.setter
    def centroid_instance(self, instance: Centroid) -> None:
        verify_type(instance, Centroid)
        self._centroid_instance = instance

    @property
    def intensity2color_instance(self) -> IntensityToColor:
        verify_none(self._intensity_to_color_instance)
        return self._intensity_to_color_instance

    @intensity2color_instance.setter
    def intensity2color_instance(self, instance: IntensityToColor) -> None:
        verify_type(instance, IntensityToColor)
        self._intensity_to_color_instance = instance

    @property
    def pswave_instance(self) -> PSWave:
        verify_none(self._pswave_instance)
        return self._pswave_instance

    @pswave_instance.setter
    def pswave_instance(self, instance: PSWave) -> None:
        verify_type(instance, PSWave)
        self._pswave_instance = instance

    @property
    def eew_debugging_enabled(self) -> bool:
        return Env.config.debug.kmoni_eew.enabled or \
               Env.config.debug.svir_eew.enabled or \
               Env.config.debug.iedred_eew.enabled


Env = _Env()
