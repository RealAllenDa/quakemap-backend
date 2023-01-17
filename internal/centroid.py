from loguru import logger

from model.centroid import CentroidModel, LatLngModel, CentroidModelWithRegion, LatLngModelWithRegion, \
    ObsStationsCentroidModel, AreaToPositionCentroidModel
from sdk import func_timer, read_csv, relpath, verify_none, todo, read_json, obj_to_model


class Centroid:
    """
    Centroid class that contains area & city centroids.
    """

    def __init__(self):
        """
        Initializes the instance.
        """
        self._area_centroid = CentroidModel()
        self._station_centroid = CentroidModelWithRegion()
        self._eq_station_centroid: list[ObsStationsCentroidModel] = []
        self._area_to_position_centroid = AreaToPositionCentroidModel()
        self._init_area_centroid()
        self._init_station_centroid()
        self._init_earthquake_station_centroid()
        self._init_area_to_position_centroid()
        logger.success("Centroid instance initialized.")

    def refresh_stations(self) -> None:
        """
        Updates intensity station names using DM-S.S.S.
        NOTE: Unused for now.
        """
        todo()

    @func_timer
    def _init_area_centroid(self) -> None:
        """
        Initializes area centroid.
        """
        content = read_csv(
            relpath("../assets/centroid/jma_area_centroid.csv"),
            fieldnames=("id", "name", "latitude", "longitude")
        )
        verify_none(content)
        for row in content:
            self._area_centroid.content[row["name"]] = LatLngModel(
                latitude=row["latitude"],
                longitude=row["longitude"]
            )

    @func_timer
    def _init_station_centroid(self) -> None:
        """
        Initializes station centroid.
        """
        content = read_csv(
            relpath("../assets/centroid/intensity_stations.csv"),
            fieldnames=("name", "region_code", "region_name", "latitude", "longitude")
        )
        verify_none(content)
        for row in content:
            self._station_centroid.content[row["name"]] = LatLngModelWithRegion(
                latitude=row["latitude"],
                longitude=row["longitude"],
                region_code=row["region_code"],
                region_name=row["region_name"]
            )

    @func_timer
    def _init_earthquake_station_centroid(self) -> None:
        """
        Initializes the centroid for observation stations.
        """
        file = read_json(
            relpath("../assets/centroid/observation_points.json")
        )
        verify_none(file)
        for i in file:
            if not (i["Point"] is None or i["IsSuspended"]):
                # noinspection PyTypeChecker
                self._eq_station_centroid.append(
                    obj_to_model(i, ObsStationsCentroidModel)
                )

    @func_timer
    def _init_area_to_position_centroid(self):
        """
        Initializes the centroid for sub region codes & position conversion.
        """
        # See AreaToPositionCentroidModel definition for further details
        # of why to do this.
        parse_dict = {
            "content": {}
        }
        raw_file = read_json(relpath("../assets/centroid/area_position.json"))
        verify_none(raw_file)
        parse_dict["content"] = raw_file

        self._area_to_position_centroid = obj_to_model(
            parse_dict,
            AreaToPositionCentroidModel
        )

    @property
    def area_centroid(self) -> CentroidModel:
        return self._area_centroid

    @property
    def station_centroid(self) -> CentroidModelWithRegion:
        return self._station_centroid

    @property
    def earthquake_station_centroid(self) -> list[ObsStationsCentroidModel]:
        return self._eq_station_centroid

    @property
    def area_position_centroid(self) -> AreaToPositionCentroidModel:
        return self._area_to_position_centroid
