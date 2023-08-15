from loguru import logger

from schemas.geojson import GeoJsonModel, TsunamiGeoJsonModel
from schemas.p2p_info import TsunamiAreaModel, TsunamiAreaGradeEnum
from sdk import func_timer, json_to_model, relpath


class GeoJson:
    """
    GeoJson class to parse earthquake areas and tsunami areas.
    """

    def __init__(self):
        """
        Initializes the instance.
        """
        self._init_json()
        logger.success("GeoJson instance initialized.")

    @func_timer
    def _init_json(self) -> None:
        self.japan_areas = json_to_model(relpath("../assets/area/japan_areas.json"), GeoJsonModel)
        self.tsunami_areas = json_to_model(relpath("../assets/area/tsunami_areas.json"), TsunamiGeoJsonModel)

    @func_timer
    def get_tsunami_geojson(self, area_grades: dict[str, TsunamiAreaModel]) -> GeoJsonModel:
        """
        Tries to get the geojson for tsunami areas.

        :param area_grades: Area warning grades
        :return: Area-Color pair
        """
        from env import Env
        return_model = GeoJsonModel()
        area_names = area_grades.keys()
        for i in self.tsunami_areas.features:
            if i.properties.name in area_names:
                # Included in the tsunami area
                try:
                    i.properties.grade = area_grades[i.properties.name].grade.value
                except Exception:
                    logger.exception(f"Failed to parse tsunami GeoJson for {i.properties.name}.")
                    i.properties.grade = TsunamiAreaGradeEnum.Unknown.value
                if i.properties.grade != TsunamiAreaGradeEnum.Unknown:
                    i.properties.intensity_color = Env.config.tsunami.color.dict().get(i.properties.grade, "")
                else:
                    logger.warning(f"{i.properties.name}: grade is unknown. Skipping parsing.")
                return_model.features.append(i)
        logger.debug("Got tsunami GeoJson.")
        return return_model
