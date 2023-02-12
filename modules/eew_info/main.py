import time
from typing import Optional

from loguru import logger

from env import Env
from model.config import EEWTargetEnum
from model.eew import KmoniTimeModel, KmoniEEWModel, EEWReturnModel, EEWAlertTypeEnum, EEWConvertedIntensityEnum, \
    KmoniReturnHypocenterModel, KmoniReturnAreaColoringModel, EEWParseReturnModel, IedredEEWModel, SvirEEWModel, \
    IedredParseStatus, EEWIntensityEnum, SvirEventType
from model.eew.eew import EEWCancelledModel
from model.eew.eew_iedred import IedredCodeStringDetail, IedredTime, IedredHypocenter, IedredLocation, \
    IedredEpicenterDepth, IedredMagnitude, IedredMaxIntensity, IedredEventType, IedredEventTypeEnum, \
    IedredForecastAreasArrival, IedredForecastAreas, IedredForecastAreasIntensity
from model.intensity2color import IntensityToColorReturnModel, AreaIntensityModel
from model.pswave import PSWaveTimeModel
from model.sdk import ResponseTypeModel, ResponseTypes
from modules.base_module import BaseModule
from sdk import func_timer, web_request, verify_none, json_to_model, relpath


class EEWInfo(BaseModule):
    """
    Earthquake Early Warning module.
    """

    def __init__(self):
        super(EEWInfo, self).__init__()
        self.info = EEWReturnModel()

    @func_timer
    def get_info(self) -> None:
        """
        Gets svir and kmoni EEW.
        """
        try:
            self._get_svir_eew()
        except Exception:
            logger.exception("Failed to get svir/iedred eew.")
        try:
            self._get_kmoni_eew()
        except Exception:
            logger.exception("Failed to get kmoni eew.")
        logger.info("Refreshed EEW info.")

    @func_timer
    def _get_svir_eew(self) -> None:
        """
        Decides which EEW to get for svir-area.
        """
        if Env.config.dmdata.enabled:
            logger.trace("Dmdata enabled. No need to fetch svir.")
            return
        if Env.config.eew.target == EEWTargetEnum.svir:
            self._real_get_svir_eew()
        elif Env.config.eew.target == EEWTargetEnum.iedred:
            self._real_get_iedred_eew()
        else:
            logger.error("Exhaustive handling of svir/iedred eew enum. "
                         "This shouldn't have happened!")

    def _real_get_iedred_eew(self) -> None:
        """
        Gets iedred EEW.
        """
        if not Env.config.debug.iedred_eew.enabled:
            iedred_eew = web_request(url="https://api.iedred7584.com/eew/json/",
                                     proxy=Env.config.proxy,
                                     response_type=ResponseTypeModel(
                                         type=ResponseTypes.json_to_model,
                                         model=IedredEEWModel
                                     ))
            verify_none(iedred_eew.status)
            iedred_eew = iedred_eew.content
        else:
            iedred_eew = json_to_model(relpath(Env.config.debug.iedred_eew.file), IedredEEWModel)
        self.parse_iedred_eew(iedred_eew)

    def _real_get_svir_eew(self) -> None:
        """
        Formats svir EEW, then parse it using iedred parser.
        """
        if not (Env.config.debug.svir_eew.file_override.enabled and Env.config.debug.svir_eew.enabled):
            svir_eew = web_request(url="https://svir.jp/eew/data.json",
                                   proxy=Env.config.proxy,
                                   response_type=ResponseTypeModel(
                                       type=ResponseTypes.json_to_model,
                                       model=SvirEEWModel
                                   ))
            verify_none(svir_eew.status)
            svir_eew = svir_eew.content
        else:
            svir_eew = json_to_model(relpath(Env.config.debug.svir_eew.file_override.file), SvirEEWModel)
        self.parse_iedred_eew(
            self._format_svir_to_iedred(svir_eew)
        )

    def _format_svir_to_iedred(self, content: SvirEEWModel) -> IedredEEWModel:
        """
        Formats svir EEW to iedred EEW.
        """
        announced_time = time.strptime(content.head.publish_time[:19], "%Y-%m-%dT%H:%M:%S")
        origin_time = time.strptime(content.body.earthquake.origin_time[:19], "%Y-%m-%dT%H:%M:%S")

        if content.body.is_end == "1":
            # Final EEW
            event_type_code = IedredEventTypeEnum.final
        else:
            # Still occurring EEW
            event_type_code = IedredEventTypeEnum.not_final

        if content.head.status == SvirEventType.cancel:
            return IedredEEWModel(
                parse_status=IedredParseStatus.success,
                event_type=IedredEventType(
                    string=SvirEventType.cancel
                )
            )
        else:
            event_type_status = SvirEventType.normal

        if content.body.earthquake.magnitude == "/./":
            magnitude = "Unknown"
        else:
            magnitude = float(content.body.earthquake.magnitude)

        return_model = IedredEEWModel(
            parse_status=IedredParseStatus.success,
            status=IedredCodeStringDetail(
                string=str(content.head.status.value)
            ),
            announced_time=IedredTime(
                time_string=time.strftime("%Y/%m/%d %H:%M:%S", announced_time),
                unix_time=int(time.mktime(announced_time))
            ),
            origin_time=IedredTime(
                time_string=time.strftime("%Y/%m/%d %H:%M:%S", origin_time),
                unix_time=int(time.mktime(origin_time))
            ),
            event_id=content.head.event_id,
            event_type=IedredEventType(
                code=event_type_code.value,
                string=event_type_status.value
            ),
            serial=content.head.serial,
            hypocenter=IedredHypocenter(
                code=content.body.earthquake.hypocenter.code,
                name=content.body.earthquake.hypocenter.name,
                is_assumption=(content.body.is_plum == "1"),
                location=IedredLocation(
                    latitude=float(content.body.earthquake.hypocenter.latitude),
                    longitude=float(content.body.earthquake.hypocenter.longitude),
                    depth=IedredEpicenterDepth(
                        depth_int=int(content.body.earthquake.hypocenter.depth),
                        depth_string=(content.body.earthquake.hypocenter.depth + "km")
                    )
                ),
                magnitude=IedredMagnitude(
                    magnitude_float=magnitude
                )
            ),
            max_intensity=IedredMaxIntensity(
                lowest=EEWIntensityEnum[content.body.intensity.max_intensity.name]
            ),
            is_warn=(content.body.is_warn == "1")
        )

        if return_model.is_warn:
            return_model.forecast_areas = []
            for i in content.body.intensity.areas:
                arrival_time = IedredForecastAreasArrival()
                if i.forecast_kind.code[1] == "9":
                    arrival_time = IedredForecastAreasArrival(
                        flag=False,
                        condition="PLUM",
                        time="Unknown"
                    )
                elif i.forecast_kind.code[1] == "0":
                    arrival_time = IedredForecastAreasArrival(
                        flag=False,
                        condition=(i.condition if i.condition is not None else "未到達と推測"),
                        time=(i.arrival_time if i.arrival_time is not None else "00:00:00")
                    )
                return_model.forecast_areas.append(IedredForecastAreas(
                    intensity=IedredForecastAreasIntensity(
                        code=i.code,
                        name=i.name,
                        lowest=EEWIntensityEnum[i.forecast_intensity.lowest.name],
                        highest=EEWIntensityEnum[i.forecast_intensity.highest.name],
                        description=i.text_intensity
                    ),
                    is_warn=(i.forecast_kind.code[0] == "1"),
                    has_arrived=arrival_time
                ))

        return return_model

    @func_timer(log_func=logger.debug)
    def parse_iedred_eew(self, content: IedredEEWModel) -> None:
        """
        Parses iedred EEW.
        """
        if content.parse_status == IedredParseStatus.failed:
            logger.warning("Failed to parse svir EEW info: parse_status is error.")
            return

        if content.event_type.string not in ["発表", "通常"]:
            logger.debug(f"EEW Cancelled: {content}")
            self.info.svir = EEWCancelledModel()
            return

        is_final = content.event_type.code != "0"
        if is_final:
            timespan = int(time.time()) + 3600 - content.announced_time.unix_time  # China time
            logger.trace(f"Svir EEW: Timespan => {timespan}")
            # Outdated report
            if not (-12 < timespan < 180):
                # >= 3 minutes
                if (not Env.config.debug.svir_eew.ignore_outdated) and \
                        Env.config.debug.svir_eew.enabled:
                    self.info.svir = None
                    return

        if content.is_warn or content.forecast_areas:
            area_intensity: dict[str, AreaIntensityModel] = {}
            for i in content.forecast_areas:
                area_intensity[i.intensity.name] = AreaIntensityModel(
                    name=i.intensity.name,
                    intensity=EEWConvertedIntensityEnum[i.intensity.highest.name],
                    is_area=True,
                    latitude=Env.centroid_instance.area_centroid.content.get(i.intensity.name).latitude,
                    longitude=Env.centroid_instance.area_centroid.content.get(i.intensity.name).longitude
                )
                if i.intensity.lg_intensity_highest is not None:
                    area_intensity[i.intensity.name].lg_intensity = i.intensity.lg_intensity_highest.value
        else:
            area_intensity = {}

        pswave_time = self._parse_pswave_time(content.origin_time.unix_time,
                                              content.hypocenter.location.depth.depth_string)
        if not pswave_time:
            logger.warning("No PSWave time available.")
            pswave_time = PSWaveTimeModel()

        self.info.svir = EEWParseReturnModel(
            status=0,
            type="svir",
            is_plum=content.hypocenter.is_assumption,
            is_cancel=False,
            is_test=(content.status.string != "通常"),
            max_intensity=EEWConvertedIntensityEnum[content.max_intensity.lowest.name],
            report_time=content.announced_time.time_string,
            report_timestamp=content.announced_time.unix_time,
            report_num=int(content.serial),
            report_flag=(EEWAlertTypeEnum.warning if content.is_warn else EEWAlertTypeEnum.forecast),
            report_id=content.event_id,
            occur_timestamp=(
                content.origin_time.unix_time if not Env.eew_debugging_enabled else int(time.time() + 3600)),
            is_final=is_final,
            magnitude=content.hypocenter.magnitude.magnitude_float,
            hypocenter=KmoniReturnHypocenterModel(
                name=content.hypocenter.name,
                longitude=content.hypocenter.location.longitude,
                latitude=content.hypocenter.location.latitude,
                depth=content.hypocenter.location.depth.depth_string
            ),
            area_intensity=None,
            area_coloring=KmoniReturnAreaColoringModel(
                areas=area_intensity,
                recommended_areas=True
            ),
            s_wave=pswave_time.s_time,
            p_wave=pswave_time.p_time
        )

    @func_timer
    def _get_kmoni_eew(self) -> None:
        """
        Gets EEW information from kmoni API.
        """
        req_date, req_time = self._fetch_kmoni_time()
        response = web_request(url=f"http://www.kmoni.bosai.go.jp/webservice/hypo/eew/{req_time}.json",
                               proxy=Env.config.proxy,
                               response_type=ResponseTypeModel(
                                   type=ResponseTypes.json_to_model,
                                   model=KmoniEEWModel
                               ))
        verify_none(response.status)
        content: KmoniEEWModel = response.content
        if content.result.message != "":
            # No EEW Available
            self.info.kmoni = None
        else:
            # EEW Available
            logger.debug("EEW available. Parsing.")
            self._parse_kmoni_eew(content, req_time, req_date)

    def _parse_kmoni_eew(self, content: KmoniEEWModel, req_time: str, req_date: str) -> None:
        """
        Parses kmoni EEW model.
        :param content: The kmoni API content
        """
        if content.is_cancel:
            self.info.kmoni = EEWCancelledModel()
            return
        if content.alert_flag == "予報":
            report_flag = EEWAlertTypeEnum.forecast
        elif content.alert_flag == "警報":
            report_flag = EEWAlertTypeEnum.warning
        else:
            logger.warning(f"Different type than forecast and warning: {content.alert_flag}")
            report_flag = EEWAlertTypeEnum.default
        parsed_intensity = EEWConvertedIntensityEnum[content.calculated_intensity.name]
        intensity_model = self._parse_eew_intensity(req_date, req_time)
        origin_time = time.strptime(content.origin_time, "%Y%m%d%H%M%S")
        origin_timestamp = int(time.mktime(origin_time))
        pswave_time = self._parse_pswave_time(origin_timestamp, content.depth)
        if not pswave_time:
            logger.warning("No PSWave time available.")
            pswave_time = PSWaveTimeModel()
        report_time = time.strptime(content.report_time, "%Y/%m/%d %H:%M:%S")
        report_timestamp = int(time.mktime(report_time))
        self.info.kmoni = EEWParseReturnModel(
            status=0,
            type="kmoni",
            is_plum=False,
            is_cancel=content.is_cancel,
            is_test=content.is_training,
            max_intensity=parsed_intensity,
            report_time=content.report_time,
            report_timestamp=report_timestamp,
            occur_timestamp=origin_timestamp,
            report_num=content.report_number,
            report_flag=report_flag,
            report_id=content.report_id,
            is_final=content.is_final,
            magnitude=content.magnitude,
            hypocenter=KmoniReturnHypocenterModel(
                name=content.region_name,
                longitude=float(content.longitude),
                latitude=float(content.latitude),
                depth=content.depth
            ),
            area_intensity=intensity_model.station_intensities,
            area_coloring=KmoniReturnAreaColoringModel(
                areas=intensity_model.area_intensities,
                recommended_areas=intensity_model.recommend_areas
            ),
            s_wave=pswave_time.s_time,
            p_wave=pswave_time.p_time
        )

    def _parse_eew_intensity(self, req_date: str, req_time: str) -> IntensityToColorReturnModel:
        """
        Parses EEW intensities from kmoni image.
        :return: station intensities, area intensities, whether to recommend area coloring
        """
        if not Env.config.debug.kmoni_eew.image_override.enabled:
            response = web_request(
                url=f"http://www.kmoni.bosai.go.jp/data/map_img/EstShindoImg/eew/{req_date}/{req_time}.eew.gif",
                proxy=Env.config.proxy,
                response_type=ResponseTypeModel(
                    type=ResponseTypes.raw_response
                )
            )
            verify_none(response.status)
            content = response.content.content
        else:
            with open(Env.config.debug.kmoni_eew.image_override.file, "rb") as f:
                content = f.read()
                f.close()

        return Env.intensity2color_instance.intensity2color(content)

    def _parse_pswave_time(self, origin_timestamp: int, depth: str) -> Optional[PSWaveTimeModel]:
        """
        Parses PSWave time.
        :return: P wave time, S wave time
        """
        try:
            if Env.eew_debugging_enabled:
                origin_timestamp = int(Env.init_time)
            time_difference = float(time.time() +
                                    # Chinese time -> Japanese time
                                    (3600 if not Env.eew_debugging_enabled else 0) -
                                    origin_timestamp)

            depth = int(depth.replace("km", ""))

            return Env.pswave_instance.parse_pswave_time(depth, time_difference)
        except Exception:
            logger.exception("Failed to parse PSWave time.")
            return None

    def _fetch_kmoni_time(self) -> tuple[str, str]:
        """
        Gets kmoni EEW time.
        :return: a time tuple: (%Y%m%d, %Y%m%d%H%M%S)
        """
        time_model = web_request(url="http://www.kmoni.bosai.go.jp/webservice/server/pros/latest.json",
                                 proxy=Env.config.proxy,
                                 response_type=ResponseTypeModel(
                                     type=ResponseTypes.json_to_model,
                                     model=KmoniTimeModel
                                 ))
        verify_none(time_model.status)

        if Env.config.debug.kmoni_eew.enabled:
            # Time between startup and now
            # In order to calculate the time elapsed to have consecutive EEWs.
            time_offset = int(time.time()) - Env.init_time

            # Construct date
            req_date: str = Env.config.debug.kmoni_eew.start_time[:8]

            # Construct time
            time_struct = time.strptime(Env.config.debug.kmoni_eew.start_time, "%Y%m%d%H%M%S")
            # Real time to send to server
            req_timestamp = time.mktime(time_struct) + time_offset
            req_time = time.strftime("%Y%m%d%H%M%S", time.localtime(req_timestamp))
        else:
            time_struct = time.strptime(time_model.content.latest_time, "%Y/%m/%d %H:%M:%S")
            req_date = time.strftime("%Y%m%d", time_struct)
            req_time = time.strftime("%Y%m%d%H%M%S", time_struct)

        return req_date, req_time
