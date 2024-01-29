import re
import time
from typing import Optional

from loguru import logger

from schemas.dmdata.generic import DmdataMessageTypes
from schemas.eew import EEWIntensityEnum, IedredForecastAreasIntensity, SvirToIntensityEnum, SvirLgToIntensityEnum, \
    IedredForecastAreas, IedredForecastAreasArrival, IedredMaxIntensity, SvirForecastLgInt, IedredMagnitude, \
    IedredEpicenterDepth, IedredLocation, IedredHypocenter, IedredEventType, IedredTime, IedredCodeStringDetail, \
    IedredParseStatus, IedredEEWModel, SvirLgIntensityEnum, IedredEventTypeEnum, SvirEventType
from schemas.jma.eew import JMAEEWApiModel
from schemas.jma.generic import JMAInfoType, JMAControlStatus
from sdk import generate_list, obj_to_model, func_timer


@func_timer(log_func=logger.debug)
def parse_eew(content: dict, eew_type: DmdataMessageTypes) -> Optional[IedredEEWModel]:
    """
    Parses EEW, converts into iedred format.
    """
    model: Optional[JMAEEWApiModel] = obj_to_model(content, JMAEEWApiModel)
    if not model:
        logger.error("Failed to parse EEW: model is None")
        return None
    report = model.report

    if report.control.status != JMAControlStatus.normal:
        logger.warning("EEW Training: Add training sign")
        event_status = SvirEventType.train
    else:
        event_status = SvirEventType.normal

    if report.head.info_status != JMAInfoType.issued:
        logger.warning("EEW Cancellation: returning cancelled model")
        return IedredEEWModel(
            parse_status=IedredParseStatus.success,
            event_type=IedredEventType(
                string=SvirEventType.cancel
            )
        )
    else:
        event_type_status = SvirEventType.normal

    announced_time = report.head.report_date.timetuple()
    if report.body.earthquake.origin_time is not None:
        origin_time = report.body.earthquake.origin_time.timetuple()
    else:
        logger.warning("EEW origin time unknown: defaulting to arrival_time")
        origin_time = report.body.earthquake.arrival_time.timetuple()

    if report.body.next_advisory:
        # Final
        event_type_code = IedredEventTypeEnum.final
    else:
        event_type_code = IedredEventTypeEnum.not_final

    if report.body.earthquake.magnitude.magnitude == "NaN" or \
            report.body.earthquake.magnitude.magnitude == "1.0":
        # Estimated/Unknown magnitude
        magnitude = "Unknown"
    else:
        magnitude = float(report.body.earthquake.magnitude.magnitude)

    is_assumption = report.body.earthquake.condition is not None
    is_warn = eew_type == DmdataMessageTypes.eew_warning
    if report.body.comments:
        if report.body.comments.warning_comment:
            is_warn = is_warn or (report.body.comments.warning_comment.code == "0201")

    hypocenter_latitude = -200
    hypocenter_longitude = -200
    hypocenter_depth = -1
    try:
        if report.body.earthquake.hypocenter.area.coordinate.description != "震源要素不明":
            match_hypocenter = r"([+-][0-9.]+)([+-][0-9.]+)([+-][0-9.]+)?"
            hypocenter_parsed = re.match(match_hypocenter,
                                         report.body.earthquake.hypocenter.area.coordinate.coordinate)
            if len(hypocenter_parsed.groups()) == 2:
                hypocenter_latitude = hypocenter_parsed.group(1)
                hypocenter_longitude = hypocenter_parsed.group(2)
            elif len(hypocenter_parsed.groups()) == 3:
                hypocenter_latitude = hypocenter_parsed.group(1)
                hypocenter_longitude = hypocenter_parsed.group(2)
                hypocenter_depth = int(int(hypocenter_parsed.group(3)) / 1000 * -1)
        else:
            logger.warning("EEW info: Unknown hypocenter")
    except Exception:
        logger.exception("EEW hypocenter: error occurred while parsing")

    if report.body.intensity:
        lowest_intensity = EEWIntensityEnum[report.body.intensity.forecast.forecast_intensity.lowest.name]
        if report.body.intensity.forecast.forecast_long_period_intensity:
            lowest_lg_intensity = SvirLgIntensityEnum[
                report.body.intensity.forecast.forecast_long_period_intensity.lowest.name]
        else:
            lowest_lg_intensity = SvirLgIntensityEnum.no
    else:
        lowest_intensity = EEWIntensityEnum.no
        lowest_lg_intensity = SvirLgIntensityEnum.no

    return_model = IedredEEWModel(
        parse_status=IedredParseStatus.success,
        status=IedredCodeStringDetail(
            string=str(event_status.value)
        ),
        announced_time=IedredTime(
            time_string=time.strftime("%Y/%m/%d %H:%M:%S", announced_time),
            unix_time=int(time.mktime(announced_time))
        ),
        origin_time=IedredTime(
            time_string=time.strftime("%Y/%m/%d %H:%M:%S", origin_time),
            unix_time=int(time.mktime(origin_time))
        ),
        event_id=report.head.event_id,
        event_type=IedredEventType(
            code=event_type_code.value,
            string=event_type_status.value
        ),
        serial=report.head.serial,
        hypocenter=IedredHypocenter(
            code=report.body.earthquake.hypocenter.area.code.code,
            name=report.body.earthquake.hypocenter.area.name,
            is_assumption=is_assumption,
            location=IedredLocation(
                latitude=float(hypocenter_latitude),
                longitude=float(hypocenter_longitude),
                depth=IedredEpicenterDepth(
                    depth_int=int(hypocenter_depth),
                    depth_string=(str(hypocenter_depth) + "km")
                )
            ),
            magnitude=IedredMagnitude(
                magnitude_float=magnitude
            )
        ),
        max_intensity=IedredMaxIntensity(
            lowest=lowest_intensity
        ),
        max_lg_intensity=SvirForecastLgInt(
            lowest=lowest_lg_intensity,
            highest=SvirLgToIntensityEnum[lowest_lg_intensity.name]
        ),
        is_warn=is_warn
    )

    if report.body.intensity is not None:
        if return_model.is_warn or (report.body.intensity.forecast.areas is not None):
            forecast_areas = generate_list(report.body.intensity.forecast.areas)
            return_model.forecast_areas = []
            for i in forecast_areas:
                if i.area.forecast_kind.kind.code[1] == "9":
                    arrival_time = IedredForecastAreasArrival(
                        flag=False,
                        condition="PLUM",
                        time="Unknown"
                    )
                else:
                    if i.area.arrival_time is not None:
                        parsed_arrival_time = time.strftime("%Y/%m/%d %H:%M:%S", i.area.arrival_time.timetuple())
                    else:
                        parsed_arrival_time = "00:00:00"
                    arrival_time = IedredForecastAreasArrival(
                        flag=False,
                        condition=(i.area.condition if i.area.condition is not None else "未到達と推測"),
                        time=parsed_arrival_time
                    )
                if i.area.forecast_intensity.highest == SvirToIntensityEnum.above:
                    i.area.forecast_intensity.highest = i.area.forecast_intensity.lowest
                forecast_intensity = IedredForecastAreasIntensity(
                    code=i.area.code,
                    name=i.area.name,
                    lowest=EEWIntensityEnum[i.area.forecast_intensity.lowest.name],
                    highest=EEWIntensityEnum[i.area.forecast_intensity.highest.name],
                    description=str(i.area.forecast_intensity.lowest.name)
                )
                if i.area.forecast_long_period_intensity is not None:
                    if i.area.forecast_long_period_intensity.highest == SvirLgToIntensityEnum.above:
                        i.area.forecast_long_period_intensity.highest = i.area.forecast_long_period_intensity.lowest

                    forecast_intensity.lg_intensity_lowest = i.area.forecast_long_period_intensity.lowest
                    forecast_intensity.lg_intensity_highest = i.area.forecast_long_period_intensity.highest
                return_model.forecast_areas.append(IedredForecastAreas(
                    intensity=forecast_intensity,
                    is_warn=(i.area.forecast_kind.kind.name == "緊急地震速報（警報）"),
                    has_arrived=arrival_time
                ))

    return return_model
