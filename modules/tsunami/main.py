import time
from datetime import datetime
from typing import Optional

import xmltodict
from loguru import logger

from env import Env
from model.dmdata.generic import DmdataMessageTypes
from model.jma import JMAList
from model.jma.tsunami_expectation import JMAMessageTypeEnum, JMATsunamiExpectationApiModel, JMAControlStatus, \
    JMATsunamiForecastModel, JMATsunamiForecastItem, JMATsunamiFirstHeightCondition, JMAInfoType
from model.jma.tsunami_watch import JMATsunamiWatchApiModel, JMAWatchMaxHeightCondition
from model.sdk import ResponseTypeModel, ResponseTypes
from model.tsunami import TsunamiExpectationReturnModel, TsunamiParseOrigin, TsunamiExpectationModel, \
    TsunamiExpectationGrade, TsunamiExpectationSpecialTimeModel, TsunamiExpectationTimeModel, \
    TsunamiExpectationHeight, TsunamiObservationReturnModel, TsunamiObservationAreaModel, \
    TsunamiObservationCondition, \
    TsunamiObservationHeightCondition
from modules.base_module import BaseModule
from sdk import func_timer, web_request, verify_none, relpath, generate_list


class TsunamiInfo(BaseModule):
    """
    Tsunami Info module.
    """

    def __init__(self):
        super().__init__()

        self.tsunami_expectation_info = TsunamiExpectationReturnModel()
        self.tsunami_obs_info = TsunamiObservationReturnModel()

        self.tsunami_watch_in_effect = False
        self.tsunami_warning_in_effect = False

        self.previous_tsunami_info: Optional[JMAList] = None

    def reload(self) -> None:
        self.tsunami_expectation_info = TsunamiExpectationReturnModel()
        self.tsunami_obs_info = TsunamiObservationReturnModel()

        self.tsunami_watch_in_effect = False
        self.tsunami_warning_in_effect = False

        self.previous_tsunami_info: Optional[JMAList] = None

    @func_timer
    def get_info(self) -> None:
        """
        Gets JMA's information list XML. (eqvol.xml)
        """
        if Env.config.dmdata.enabled:
            logger.trace("No need to update tsunami.")
            return
        response = web_request(url="https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml",
                               proxy=Env.config.proxy,
                               response_type=ResponseTypeModel(
                                   type=ResponseTypes.xml_to_model,
                                   model=JMAList
                               ))
        verify_none(response.status)
        self.parse_jma_list(response.content)

    @func_timer
    def parse_jma_list(self, content: JMAList) -> None:
        """
        Parses JMA list.
        :param content: The JMA list model
        """
        if self.previous_tsunami_info is None:
            logger.debug("New JMA XML updated. Parsing messages.")
        elif self.previous_tsunami_info.dict() != content.dict():
            logger.debug("New JMA XML updated. Parsing messages.")
        elif not Env.config.debug.tsunami.enabled:
            logger.debug("No new JMA XML info.")
            return

        info_urls = {}
        watch_urls = {}
        for i in content.feed.entry:
            # Omit already parsed ones
            if self.previous_tsunami_info is not None:
                if i in self.previous_tsunami_info.feed.entry:
                    logger.trace(f"Already parsed {i.id}. Skipping.")
                    continue

            # Url format: https://<url>/developer/xml/data/<id>
            # Id format: <yyyyMMddhhmmss>_<typically 0>_<id>_<code>.xml
            # Url storage: { url: time } in info_urls and watch_urls
            id = i.id.split("/")[-1]

            message_time = int(id.split("_")[0])
            message_type = JMAMessageTypeEnum(id.split("_")[2])
            if message_type == JMAMessageTypeEnum.tsunami_information:
                info_urls[i.id] = message_time
            elif message_type == JMAMessageTypeEnum.tsunami_watch:
                watch_urls[i.id] = message_time

        # Set previous XML to current one
        self.previous_tsunami_info = content

        if (not info_urls) and (not Env.config.debug.tsunami.enabled) and \
                (not watch_urls) and (not Env.config.debug.tsunami_watch.enabled):
            logger.debug("No tsunami warning in effect.")
            return

        """
        TE: Tsunami Expectation Information
        TW: Tsunami Watch Information
        
        In case of a tsunami, the messages' sequence would look like this:
            TE1 ---> TW1+TW2 ---> TE2 ---> TW3 and so on.
        We only need to parse the latest TE, since all warnings/advisories are contained.
        However, we need to pass all the new TWs to the getter, 
         since every TW represents different information section.
            e.g. TW1: Information about high tide time, etc.    <---- Omit
                 TW2: Information about tsunami observations    <---- Not latest - Omit
                 TW3: Information about tsunami observations    <---- Parse!
        
        Moreover, we need to parse TE first, then parse TWs, since TWs contain updated tsunami warnings/advisories.
        """
        if not Env.config.debug.tsunami.enabled and not Env.config.debug.tsunami_watch.enabled:
            latest_info_url = max(info_urls, key=lambda x: info_urls[x])
        else:
            latest_info_url = "TEST_TE"
        logger.debug(f"Parsing tsunami expectation file {latest_info_url}")

        # Parse TE first!
        self.get_tsunami_expectation(latest_info_url)
        if watch_urls or Env.config.debug.tsunami_watch.enabled:
            if not Env.config.debug.tsunami_watch.enabled:
                # Sort by time
                watch_info_urls = sorted(watch_urls, key=lambda x: watch_urls[x])
            else:
                watch_info_urls = ["TEST"]
            # Parse the latest first.
            self.get_tsunami_watch(list(reversed(watch_info_urls)))

    def parse_dmdata(self, xml_message: dict, parse_type: DmdataMessageTypes):
        """Parses dmdata messages.
        :param xml_message: The message
        :param parse_type: Tsunami expectation/watch information"""
        if parse_type == DmdataMessageTypes.tsunami_warning:
            content = JMATsunamiExpectationApiModel.parse_obj(xml_message)
            if content.report.control.status != JMAControlStatus.normal:
                logger.warning(f"Drill/Other tsunami message: {content.report.control.status.name}. Skipped.")
                return
            self.parse_tsunami_expectation(
                content.report.body.tsunami.forecast,
                TsunamiParseOrigin.tsunami_expectation,
                content.report.head.report_date
            )
        elif parse_type == DmdataMessageTypes.tsunami_info:
            content = JMATsunamiWatchApiModel.parse_obj(xml_message)
            if content.report.head.title == "津波観測に関する情報":
                if content.report.control.status == JMAControlStatus.normal and \
                        content.report.head.info_status == JMAInfoType.issued:
                    self.parse_tsunami_expectation(
                        content.report.body.tsunami.forecast,
                        TsunamiParseOrigin.tsunami_watch,
                        content.report.head.report_date
                    )
                    # Parse observation information
                    self.parse_tsunami_observation(content)
        else:
            logger.error("Exhaustive handling of parse_type")

    def get_tsunami_expectation(self, info_url: str) -> None:
        """
        Gets tsunami expectation XML.
        :param info_url: XML link
        """
        if not Env.config.debug.tsunami.enabled:
            response = web_request(info_url,
                                   proxy=Env.config.proxy,
                                   response_type=ResponseTypeModel(
                                       type=ResponseTypes.xml_to_model,
                                       model=JMATsunamiExpectationApiModel
                                   ))
            if not response.status:
                logger.error("Failed to fetch tsunami expectation")
                return
            content: JMATsunamiExpectationApiModel = response.content
        else:
            with open(relpath(Env.config.debug.tsunami.file), encoding="utf-8") as f:
                response = xmltodict.parse(f.read(), encoding="utf-8")
                content = JMATsunamiExpectationApiModel.parse_obj(response)
                f.close()
        if content.report.control.status != JMAControlStatus.normal:
            logger.warning(f"Drill/Other tsunami message: {content.report.control.status.name}. Skipped.")
            return
        self.parse_tsunami_expectation(
            content.report.body.tsunami.forecast,
            TsunamiParseOrigin.tsunami_expectation,
            content.report.head.report_date
        )

    @func_timer
    def parse_tsunami_expectation(self,
                                  content: JMATsunamiForecastModel,
                                  origin: TsunamiParseOrigin,
                                  receive_time: datetime) -> None:
        """
        Parses tsunami expectation.

        :param receive_time: The receive time
        :param origin: The tsunami forecast model
        :param content: Converted TE model
        """
        tsunami_items = generate_list(content.item)
        receive_time = time.strftime("%Y/%m/%d %H:%M:%S", receive_time.timetuple())
        areas, forecast_areas = self.parse_tsunami_areas(tsunami_items)

        # noinspection PyTypeChecker
        self.tsunami_expectation_info = TsunamiExpectationReturnModel(
            receive_time=receive_time,
            origin=origin.value,
            areas=areas,
            forecast_areas=forecast_areas
        )

    def parse_tsunami_areas(self, items: list[JMATsunamiForecastItem]) \
            -> tuple[list[TsunamiExpectationModel], list[TsunamiExpectationModel]]:
        """
        Parses tsunami areas.

        :param items: tsunami items in JMA XML
        :return: list of tsunami areas
        """
        area_list: list[TsunamiExpectationModel] = []
        forecast_list: list[TsunamiExpectationModel] = []
        for i in items:
            if i.category.kind.name in ["津波注意報解除", "警報解除"]:
                # Cancellation of advisory/warning
                continue

            # Name
            area_name = i.area.name

            # Grade
            if "大津波警報" in i.category.kind.name:
                area_grade = TsunamiExpectationGrade.major_warning
            elif "津波警報" in i.category.kind.name:
                area_grade = TsunamiExpectationGrade.warning
            elif "津波注意報" in i.category.kind.name:
                area_grade = TsunamiExpectationGrade.watch
            elif "津波予報（若干の海面変動）" in i.category.kind.name:
                area_grade = TsunamiExpectationGrade.forecast
            else:
                area_grade = TsunamiExpectationGrade.unknown

            # Time
            area_time = TsunamiExpectationSpecialTimeModel(
                type="no_time",
                time="Unknown",
                status=-1
            )
            if area_grade not in [TsunamiExpectationGrade.forecast, TsunamiExpectationGrade.unknown]:
                first_time_estimation = i.first_height
                if first_time_estimation is not None:
                    if first_time_estimation.condition is not None:
                        if first_time_estimation.condition == JMATsunamiFirstHeightCondition.arriving_now:
                            area_time = TsunamiExpectationSpecialTimeModel(
                                type="no_time",
                                time="Arriving Now",
                                status=0
                            )
                        elif first_time_estimation.condition == JMATsunamiFirstHeightCondition.arrival_expected:
                            area_time = TsunamiExpectationSpecialTimeModel(
                                type="no_time",
                                time="Arrival Expected",
                                status=1
                            )
                        elif first_time_estimation.condition == JMATsunamiFirstHeightCondition.arrived:
                            area_time = TsunamiExpectationSpecialTimeModel(
                                type="no_time",
                                time="Arrived",
                                status=2
                            )
                        else:
                            logger.error("Exhaustive handling of first_time->condition")
                    else:
                        area_time = TsunamiExpectationTimeModel(
                            type="time",
                            time=time.strftime("%m-%d %H:%M", first_time_estimation.arrival_time.timetuple()),
                            timestamp=int(time.mktime(first_time_estimation.arrival_time.timetuple()))
                        )
                else:
                    logger.error(f"Failed to parse first height for {area_name}: is None")

            # Height
            area_height = TsunamiExpectationHeight.unknown
            if i.max_height is not None:
                max_height = i.max_height.height
                try:
                    area_height = TsunamiExpectationHeight[max_height.description.name]
                except Exception:
                    logger.exception("Failed to parse max height.")
            else:
                logger.warning(f"Area height is unknown: {area_name}")

            area_info = TsunamiExpectationModel(
                name=area_name,
                grade=area_grade,
                height=area_height,
                time=area_time
            )

            if "津波予報（若干の海面変動）" in i.category.kind.name:
                forecast_list.append(area_info)
            else:
                area_list.append(area_info)

        self.tsunami_watch_in_effect = len(forecast_list) > 0
        self.tsunami_warning_in_effect = len(area_list) > 0

        return area_list, forecast_list

    @func_timer
    def get_tsunami_watch(self, watch_urls: list[str]) -> None:
        """
        Gets tsunami watch information.

        :param watch_urls: The tsunami watch URLs
        """
        to_parse_content: Optional[JMATsunamiWatchApiModel] = None
        if not Env.config.debug.tsunami_watch.enabled:
            for i in watch_urls:
                response = web_request(i,
                                       proxy=Env.config.proxy,
                                       response_type=ResponseTypeModel(
                                           type=ResponseTypes.xml_to_model,
                                           model=JMATsunamiWatchApiModel
                                       ))
                if not response.status:
                    logger.error("Failed to fetch tsunami watch.")
                    continue
                content: JMATsunamiWatchApiModel = response.content

                # Is it information about tsunami observations?
                if content.report.head.title == "津波観測に関する情報":
                    # Normal info?
                    if content.report.control.status == JMAControlStatus.normal and \
                            content.report.head.info_status == JMAInfoType.issued:
                        logger.info(f"Parsing watch url: {i}")
                        to_parse_content = content
                        # Do not need to continue
                        break
        else:
            with open(relpath(Env.config.debug.tsunami_watch.file), encoding="utf-8") as f:
                response = xmltodict.parse(f.read(), encoding="utf-8")
                to_parse_content = JMATsunamiWatchApiModel.parse_obj(response)
                f.close()
        if not to_parse_content:
            logger.debug("No tsunami watch information.")
            return
        # Parse tsunami information
        self.parse_tsunami_expectation(
            to_parse_content.report.body.tsunami.forecast,
            TsunamiParseOrigin.tsunami_watch,
            to_parse_content.report.head.report_date
        )
        # Parse observation information
        self.parse_tsunami_observation(to_parse_content)

    @func_timer
    def parse_tsunami_observation(self, content: JMATsunamiWatchApiModel) -> None:
        """
        Parses tsunami observation information.

        :param content: The observation information
        """
        areas: list[TsunamiObservationAreaModel] = []

        receive_time = time.strftime("%Y/%m/%d %H:%M:%S", content.report.head.report_date.timetuple())
        items = generate_list(content.report.body.tsunami.observation.item)

        for i in items:
            stations = generate_list(i.station)
            for j in stations:
                # Has condition?
                if j.max_height.condition is not None:
                    if j.max_height.condition == JMAWatchMaxHeightCondition.observing:
                        areas.append(TsunamiObservationAreaModel(
                            name=j.name,
                            time="None",
                            condition=TsunamiObservationCondition.observing,
                            height="None",
                            height_condition=TsunamiObservationHeightCondition.none,
                            height_is_max=False
                        ))
                        continue
                    elif j.max_height.condition == JMAWatchMaxHeightCondition.weak:
                        time_formatted = time.strftime("%m-%d %H:%M", j.max_height.date.timetuple())
                        areas.append(TsunamiObservationAreaModel(
                            name=j.name,
                            time=time_formatted,
                            condition=TsunamiObservationCondition.weak,
                            height="None",
                            height_condition=TsunamiObservationHeightCondition.none,
                            height_is_max=False
                        ))
                        continue

                time_formatted = time.strftime("%m-%d %H:%M", j.max_height.date.timetuple())

                try:
                    max_height = j.max_height.height

                    # Height condition
                    if max_height.condition is not None:
                        height_condition = TsunamiObservationHeightCondition[max_height.condition.name]
                    else:
                        height_condition = TsunamiObservationHeightCondition.none

                    # Max height & height
                    height = max_height.text
                    height_is_max = ("以上" in max_height.description)
                except Exception:
                    logger.exception(f"Failed to parse tsunami area: {j.name}")
                    continue

                areas.append(TsunamiObservationAreaModel(
                    name=j.name,
                    time=time_formatted,
                    condition=TsunamiObservationCondition.none,
                    height=height,
                    height_condition=height_condition,
                    height_is_max=height_is_max
                ))

        self.tsunami_obs_info = TsunamiObservationReturnModel(
            areas=areas,
            receive_time=receive_time
        )
