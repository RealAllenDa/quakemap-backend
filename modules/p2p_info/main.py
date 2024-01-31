import json

from loguru import logger

from env import Env
from modules.base_module import BaseModule
from schemas.config import RunEnvironment
from schemas.p2p_info import P2PQuakeModel, P2PTsunamiModel, EarthquakeIntensityEnum, EarthquakeTsunamiCommentsModel, \
    EarthquakeForeignTsunamiEnum, EarthquakeDomesticTsunamiEnum, EarthquakeReturnEpicenterModel, \
    EarthquakeIssueTypeEnum, EarthquakeReturnModel, EarthquakeAreaIntensityParsingModel, \
    EarthquakeAreaIntensityPointModel, EarthquakeStationIntensityPointModel, EarthquakeAreaIntensityModel, \
    P2PTotalInfoModel, TsunamiReturnModel, P2PEarthquakePoints
from schemas.p2p_info import TsunamiAreaModel
from schemas.sdk import ResponseTypeModel, ResponseTypes
from sdk import func_timer, web_request, verify_none, relpath


class P2PInfo(BaseModule):
    """
    Earthquake Info module.
    """

    def __init__(self):
        super().__init__()
        self._last_response_list = []
        self.info = P2PTotalInfoModel()
        self.fetched_once = False
        self.previous_eq_info: list[EarthquakeReturnModel] = []

    def reload(self):
        self._last_response_list = []
        self.info = P2PTotalInfoModel()
        self.fetched_once = False

    @func_timer
    def get_info(self) -> None:
        """
        Gets P2PQuake's JSON telegram.
        """
        if Env.config.dmdata.enabled and self.fetched_once and not Env.run_env == RunEnvironment.testing:
            if Env.dmdata_instance.status.status == "OK":
                logger.trace("DMData OK. No need to fetch P2P.")
                return
        if not Env.config.debug.p2p_info.enabled:
            response = web_request(url="https://api.p2pquake.net/v2/history?codes=551&codes=552&limit=5",
                                   response_type=ResponseTypeModel(
                                       type=ResponseTypes.json  # Because the model is too complicated.
                                   ),
                                   max_retries=1,
                                   proxy=Env.config.proxy)
            verify_none(response.status)
            self.parse_info(response.content)
            self.fetched_once = True
        else:
            with open(relpath(Env.config.debug.p2p_info.file), encoding="utf-8") as f:
                content = json.loads(f.read())
                self.parse_info(content)
                f.close()

    def parse_info(self, content: list) -> None:
        if not self._last_response_list:
            # First time parsing
            parsing_list = [content[0]]
            logger.debug("First time parsing. Defaulted to the first message.")
        elif self._last_response_list != content:
            logger.debug("New earthquake information incoming. Splitting message.")
            parsing_list = [y for y in content if y not in self._last_response_list]
            logger.debug("Spilt message. Parsing now.")
        else:
            # We assume that return_list is not None.
            # Because no new information is coming, we chose not to parse it again.
            logger.debug("No new earthquake information.")
            return
        self._last_response_list = content
        # Reset content
        self.info = P2PTotalInfoModel()
        for i in reversed(parsing_list):
            if i["code"] == 551:
                self._parse_earthquake_info(i)
        # Why parse content without splitting?
        # Edge cases: There comes a possibility of tsunami information not being registered.
        for j in reversed(content):
            if j["code"] == 552:
                self._parse_tsunami_info(j)
        logger.info("Refreshed P2P info.")

    def cancel_earthquake_info(self) -> None:
        """Clears earthquake info and issues a cancellation message."""
        self.revert_earthquake_info()

    def set_earthquake_info(self, eq_list: list[EarthquakeReturnModel]) -> None:
        """Sets earthquake info."""
        self.previous_eq_info = self.info.earthquake
        self.info.earthquake = eq_list

    def revert_earthquake_info(self) -> None:
        """Reverts earthquake info in case of a cancellation."""
        if not self.previous_eq_info:
            # two ways it can happen:
            # 1. race condition where a cancellation message is issued before P2P initialized
            # 2. cancellation following another cancellation message
            # both cases are extremely edge and very improbable, thus we just throw an error and do nothing.
            logger.error("Try to revert to an empty earthquake info!")
            return
        self.info.earthquake = self.previous_eq_info
        self.previous_eq_info = []  # previous earthquake info's previous info which we didn't save

    def get_earthquake_info(self) -> list[EarthquakeReturnModel]:
        return self.info.earthquake

    @func_timer
    def _parse_earthquake_info(self, content: dict) -> None:
        """
        Parses the P2P earthquake info.
        :param content: The raw earthquake information
        """
        try:
            model: P2PQuakeModel = P2PQuakeModel.model_validate(content)
        except Exception:
            logger.exception("An unexpected error occurred while parsing P2P earthquake info.")
            return
        logger.debug(f"Parsing P2P earthquake info id: {model.id} from {model.time}.")

        # --- Pre-parse validation
        if model.issue.source == "TR.tr(\\":
            logger.debug("Training message. Skipped.")
            return
        if model.issue.type == "Other":
            logger.debug("Other earthquake message. Skipped.")
            return

        # --- Basic parameters
        if model.earthquake.hypocenter.depth == 0:
            parsed_depth = "Shallow"
        elif model.earthquake.hypocenter.depth != -1:
            parsed_depth = f"{model.earthquake.hypocenter.depth}km"
        else:
            parsed_depth = "Unknown"
        magnitude = str(round(model.earthquake.hypocenter.magnitude, 1))
        max_intensity = EarthquakeIntensityEnum[model.earthquake.max_scale.name]
        epicenter = EarthquakeReturnEpicenterModel(
            depth=parsed_depth,
            name=model.earthquake.hypocenter.name,
            latitude=model.earthquake.hypocenter.latitude,
            longitude=model.earthquake.hypocenter.longitude
        )

        # --- Tsunami comments
        tsunami_comment = EarthquakeTsunamiCommentsModel(
            domestic=EarthquakeDomesticTsunamiEnum.Unknown,
            foreign=EarthquakeForeignTsunamiEnum.Unknown
        )
        if model.earthquake.foreign_tsunami not in [
            EarthquakeForeignTsunamiEnum.No,
            EarthquakeForeignTsunamiEnum.Unknown
        ]:
            tsunami_comment.foreign = model.earthquake.foreign_tsunami
        else:
            tsunami_comment.foreign = EarthquakeForeignTsunamiEnum.No

        if model.earthquake.domestic_tsunami in [
            EarthquakeDomesticTsunamiEnum.Unknown,
            EarthquakeForeignTsunamiEnum.Checking
        ]:
            tsunami_comment.domestic = EarthquakeDomesticTsunamiEnum.Checking
        elif model.earthquake.domestic_tsunami in [
            EarthquakeDomesticTsunamiEnum.Watch,
            EarthquakeDomesticTsunamiEnum.Warning
        ]:
            tsunami_comment.domestic = EarthquakeDomesticTsunamiEnum.Warning
        else:
            tsunami_comment.domestic = model.earthquake.domestic_tsunami

        # --- Area intensity parsing
        if model.issue.type != EarthquakeIssueTypeEnum.Foreign:
            area_intensity = self.parse_area_intensity(model.points)
        else:
            logger.debug("Earthquake is foreign. Skipped area intensity parsing.")
            area_intensity = {}

        # --- Clear hypocenter info in case of IntensityReport.
        if self._is_intensity_report_data(model):
            # Blank the epicenter
            epicenter = {}

        # --- Tidy up information
        self.info.earthquake.append(EarthquakeReturnModel(
            id=model.id,
            type=model.issue.type,
            occur_time=model.earthquake.time,
            receive_time=model.time,
            magnitude=magnitude,
            max_intensity=max_intensity,
            tsunami_comments=tsunami_comment,
            hypocenter=epicenter,
            area_intensity=area_intensity
        ))
        self.previous_eq_info = self.info.earthquake
        logger.debug(f"Parsed P2P earthquake info id: {model.id} from {model.time}.")

    @func_timer
    def _parse_tsunami_info(self, content: dict) -> None:
        """
        Parses the P2P tsunami info.
        :param content: The raw tsunami information
        """
        try:
            model = P2PTsunamiModel.model_validate(content)
        except Exception:
            logger.exception("An unexpected exception occurred while parsing P2P tsunami info.")
            return
        self.info.tsunami = {}
        if model.issue.type != "Focus":
            logger.warning("Failed to parse P2P tsunami information: Information type isn't focus.")
            logger.debug(f"Info type: {model.issue.type} vs focus")
        if model.cancelled:
            self.info.tsunami_in_effect = "0"
            return
        self.info.tsunami_in_effect = "1"
        tsunami_areas: dict[str, TsunamiAreaModel] = {}
        for i in model.areas:
            tsunami_areas[i.name] = i
        self.info.tsunami = TsunamiReturnModel(
            time=model.time,
            areas=Env.geojson_instance.get_tsunami_geojson(tsunami_areas)
        )
        logger.debug(f"Parsed P2P tsunami info id: {model.id} from {model.time}.")

    def _is_intensity_report_data(self, content: P2PQuakeModel) -> bool:
        """
        Verifies if the model is an intensity report.
        :param content: The P2PQuakeModel
        """
        if content.earthquake.hypocenter.latitude == -200 or \
                content.earthquake.hypocenter.longitude == -200 or \
                content.earthquake.hypocenter.depth == -1 or \
                content.earthquake.hypocenter.magnitude == -1 or \
                content.issue.type == EarthquakeIssueTypeEnum.ScalePrompt:
            if content.issue.type != EarthquakeIssueTypeEnum.Foreign:
                return True
        return False

    @func_timer
    def parse_area_intensity(self, points: list[P2PEarthquakePoints]) -> EarthquakeAreaIntensityModel:
        """
        Parses the earthquake's area intensities.
        :param points: The P2PQuakeModel's points
        :return: The area intensity model
        """
        earthquake_area_intensity = EarthquakeAreaIntensityParsingModel()
        # --- Pre-parse: Combine intensities with names and centroids.
        for i in points:
            if i.is_area:
                # Area parsing
                point = Env.centroid_instance.area_centroid.content.get(i.address, None)
                if point is None:
                    # Very common, but ensure that we leave a trace.
                    logger.trace(f"{i.prefecture}:{i.address} with is_area {i.is_area}, intensity {i.scale} "
                                 f"was not being parsed because no points are associated with it.")
                    continue
                earthquake_area_intensity.content[i.address] = EarthquakeAreaIntensityPointModel(
                    name=i.address,
                    intensity=EarthquakeIntensityEnum[i.scale.name],
                    latitude=str(point.latitude),
                    longitude=str(point.longitude),
                    is_area=True,
                    intensity_code=i.scale
                )
            else:
                # Station parsing
                point = Env.centroid_instance.station_centroid.content.get(i.address, None)
                if point is None:
                    # Very common, but ensure that we leave a trace.
                    logger.trace(f"{i.prefecture}:{i.address} with is_area {i.is_area}, intensity {i.scale} "
                                 f"was not being parsed because no points are associated with it.")
                    continue
                earthquake_area_intensity.content[i.address] = EarthquakeStationIntensityPointModel(
                    name=i.address,
                    intensity=EarthquakeIntensityEnum[i.scale.name],
                    latitude=str(point.latitude),
                    longitude=str(point.longitude),
                    is_area=False,
                    region_code=point.region_code,
                    region_name=point.region_name,
                    intensity_code=i.scale
                )

        # --- Parsing: Either
        #               - Returns as-is, or
        #               - Combines station intensities to area intensities
        area_intensities: dict[str, EarthquakeAreaIntensityPointModel] = {}
        station_intensities: dict[str, EarthquakeStationIntensityPointModel] = {}
        for j in earthquake_area_intensity.content.keys():
            content = earthquake_area_intensity.content[j]
            if content.is_area:
                area_intensities[content.name] = content
            else:
                station_intensities[content.name] = content

                if content.region_name not in area_intensities:
                    position = Env.centroid_instance.area_position_centroid.content.get(content.region_code).position
                    area_intensities[content.region_name] = EarthquakeAreaIntensityPointModel(
                        name=content.region_name,
                        intensity=EarthquakeIntensityEnum[content.intensity_code.name],
                        latitude=str(position[0]),
                        longitude=str(position[1]),
                        is_area=True,
                        intensity_code=content.intensity_code
                    )
                else:
                    # Whether the current station's intensity is bigger than the whole area's intensity.
                    if content.intensity_code > area_intensities[content.region_name].intensity_code:
                        area_intensities[content.region_name].intensity_code = content.intensity_code
                        area_intensities[content.region_name].intensity = EarthquakeIntensityEnum[
                            content.intensity_code.name]

        return EarthquakeAreaIntensityModel(
            areas=area_intensities,
            station=station_intensities
        )
