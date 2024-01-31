import re
import time
from datetime import datetime
from typing import Optional

from loguru import logger

from schemas.dmdata.generic import DmdataMessageTypes
from schemas.jma.earthquake.destination import JMADestinationModel
from schemas.jma.earthquake.epicenter_update import JMAEpicenterUpdateModel
from schemas.jma.earthquake.generic import JMAIntensityEnum
from schemas.jma.earthquake.intensity_destination import JMAIntDestModel
from schemas.jma.earthquake.intensity_report import JMAIntReportModel
from schemas.jma.generic import JMAInfoType
from schemas.p2p_info import EarthquakeReturnModel, EarthquakeIssueTypeEnum, EarthquakeScaleEnum, \
    EarthquakeReturnEpicenterModel, P2PEarthquakePoints, EarthquakePointsScaleEnum, EarthquakeForeignTsunamiEnum, \
    EarthquakeIntensityEnum, EarthquakeTsunamiCommentsModel, EarthquakeDomesticTsunamiEnum
from sdk import func_timer, obj_to_model, generate_list


@func_timer(log_func=logger.debug)
def parse_earthquake(content: dict, earthquake_type: DmdataMessageTypes) -> EarthquakeReturnModel | str:
    """Parses earthquake nad converts it into a P2PQuakeModel."""
    if earthquake_type == DmdataMessageTypes.eq_intensity_report:
        model: Optional[JMAIntReportModel] = obj_to_model(content["Report"], JMAIntReportModel)
        earthquake_issue_type = EarthquakeIssueTypeEnum.ScalePrompt
    elif earthquake_type == DmdataMessageTypes.eq_destination:
        model: Optional[JMADestinationModel] = obj_to_model(content["Report"], JMADestinationModel)
        earthquake_issue_type = EarthquakeIssueTypeEnum.Destination
    elif earthquake_type == DmdataMessageTypes.eq_intensity_destination:
        model: Optional[JMAIntDestModel] = obj_to_model(content["Report"], JMAIntDestModel)
        if model.head.title == "遠地地震に関する情報" or not model.body.intensity:
            earthquake_issue_type = EarthquakeIssueTypeEnum.Foreign
        else:
            earthquake_issue_type = EarthquakeIssueTypeEnum.DetailScale
    elif earthquake_type == DmdataMessageTypes.eq_destination_change:
        model: Optional[JMAEpicenterUpdateModel] = obj_to_model(content["Report"], JMAEpicenterUpdateModel)
        # fixme: it does not do anything!
        return "None"
    else:
        logger.error(f"Exhaustive handling of earthquake_type: {earthquake_type}")
        return "None"

    if not model:
        logger.error("Failed to parse earthquake: model is None")
        return "None"
    if model.head.info_status == JMAInfoType.cancel:
        logger.warning(f"Rare cancellation message of {model.head.event_id} -> {model.head.report_date}")
        return "Cancel"

    hypocenter = {}
    max_scale = EarthquakeScaleEnum.no
    magnitude = -1

    # Epicenter
    if earthquake_type != DmdataMessageTypes.eq_intensity_report:
        # with hypocenter info
        hypocenter_latitude = -200
        hypocenter_longitude = -200
        hypocenter_depth = -1
        try:
            if model.body.earthquake.hypocenter.area.coordinate.description != "震源要素不明":
                match_hypocenter = r"([+-][0-9.]+)([+-][0-9.]+)([+-][0-9.]+)?"
                hypocenter_parsed = re.match(match_hypocenter,
                                             model.body.earthquake.hypocenter.area.coordinate.coordinate)
                if len(hypocenter_parsed.groups()) == 2:
                    hypocenter_latitude = hypocenter_parsed.group(1)
                    hypocenter_longitude = hypocenter_parsed.group(2)
                elif len(hypocenter_parsed.groups()) == 3 and hypocenter_parsed.group(3) is not None:
                    hypocenter_latitude = hypocenter_parsed.group(1)
                    hypocenter_longitude = hypocenter_parsed.group(2)
                    hypocenter_depth = int(int(hypocenter_parsed.group(3)) / 1000 * -1)
            else:
                logger.warning("Earthquake info: Unknown hypocenter")
        except Exception:
            logger.exception("Earthquake hypocenter: error occurred while parsing")

        if model.body.earthquake.magnitude.magnitude == "NaN":
            if model.body.earthquake.magnitude.description == "Ｍ８を超える巨大地震":
                magnitude = "Over 8"
        else:
            magnitude = model.body.earthquake.magnitude.magnitude

        if hypocenter_depth == 0:
            parsed_depth = "Shallow"
        elif hypocenter_depth != -1:
            parsed_depth = f"{hypocenter_depth}km"
        elif hypocenter_depth == 700:
            parsed_depth = f"Over 700km"
        else:
            parsed_depth = "Unknown"

        hypocenter = EarthquakeReturnEpicenterModel(
            depth=parsed_depth,
            name=model.body.earthquake.hypocenter.area.name,
            latitude=hypocenter_latitude,
            longitude=hypocenter_longitude
        )

    # Max intensity
    if earthquake_type != DmdataMessageTypes.eq_destination and \
            earthquake_type != DmdataMessageTypes.eq_destination_change and \
            earthquake_issue_type != EarthquakeIssueTypeEnum.Foreign:
        if model.body.intensity.observation.max_intensity == JMAIntensityEnum.no or \
                model.body.intensity.observation.max_intensity == JMAIntensityEnum.bigger_than_five_lower:
            logger.warning("Rare case where intensity unknown/higher than five lower in max_intensity")
        else:
            max_scale = EarthquakeScaleEnum[model.body.intensity.observation.max_intensity.name]

    # Points
    points: list[P2PEarthquakePoints] = []
    if earthquake_issue_type == EarthquakeIssueTypeEnum.ScalePrompt:
        items = generate_list(model.body.intensity.observation.pref)
        for i in items:
            areas = generate_list(i.area)
            for j in areas:
                points.append(P2PEarthquakePoints(
                    is_area=True,
                    scale=EarthquakePointsScaleEnum[j.max_intensity.name],
                    address=j.name,
                    prefecture=i.name
                ))
    elif earthquake_issue_type == EarthquakeIssueTypeEnum.DetailScale:
        items = generate_list(model.body.intensity.observation.pref)
        for i in items:
            areas = generate_list(i.area)
            for j in areas:
                cities = generate_list(j.city)
                for k in cities:
                    intensity_stations = generate_list(k.intensity_stations)
                    for station in intensity_stations:
                        points.append(P2PEarthquakePoints(
                            is_area=False,
                            scale=EarthquakePointsScaleEnum[station.intensity.name],
                            address=station.name.replace("＊", ""),
                            prefecture=i.name
                        ))

    # Tsunami
    domestic_tsunami = _domestic_tsunami(model, earthquake_issue_type)
    if earthquake_issue_type != EarthquakeIssueTypeEnum.Foreign:
        foreign_tsunami = EarthquakeForeignTsunamiEnum.No
    else:
        foreign_tsunami = _foreign_tsunami(model)

    # Time
    if earthquake_issue_type != EarthquakeIssueTypeEnum.ScalePrompt:
        earthquake_time = time.strftime("%Y/%m/%d %H:%M:%S", model.body.earthquake.arrival_time.timetuple())
    else:
        earthquake_time = time.strftime("%Y/%m/%d %H:%M:%S", model.head.target_date.timetuple())

    from internal.modules_init import module_manager
    return EarthquakeReturnModel(
        id=model.head.event_id,
        type=earthquake_issue_type,
        occur_time=earthquake_time,
        receive_time=datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")[:-3],
        magnitude=str(magnitude),
        max_intensity=EarthquakeIntensityEnum[max_scale.name],
        tsunami_comments=EarthquakeTsunamiCommentsModel(
            domestic=domestic_tsunami,
            foreign=foreign_tsunami
        ),
        hypocenter=hypocenter,
        area_intensity=module_manager.classes["p2p_info"].parse_area_intensity(points)
    )


def _domestic_tsunami(model: JMADestinationModel | JMAIntDestModel | JMAEpicenterUpdateModel,
                      issue_type: EarthquakeIssueTypeEnum) \
        -> EarthquakeDomesticTsunamiEnum:
    """Determines whether there was a tsunami or not."""
    if not model.body.comments.forecast_comment:
        logger.error("Not cancelled but no forecast_comment")
        return EarthquakeDomesticTsunamiEnum.Unknown
    code = model.body.comments.forecast_comment.code
    text = model.body.comments.forecast_comment.text
    if "0215" in code or "0230" in code:
        return EarthquakeDomesticTsunamiEnum.No
    if "0212" in code or "0213" in code or "0214" in code:
        return EarthquakeDomesticTsunamiEnum.NonEffective
    if "0211" in code:
        return EarthquakeDomesticTsunamiEnum.Warning
    if "0217" in code or "0229" in code:
        return EarthquakeDomesticTsunamiEnum.Checking

    logger.error(f"Falling back to string parsing: got code {code}")
    # Fallback - wouldn't be used in most of the time
    if issue_type == EarthquakeIssueTypeEnum.Foreign:
        if "津波の心配はありません" in text or "津波の影響はありません" in text:
            return EarthquakeDomesticTsunamiEnum.No
        if "若干の海面変動" in text:
            return EarthquakeDomesticTsunamiEnum.NonEffective
        if "調査中です" in text:
            return EarthquakeDomesticTsunamiEnum.Checking
    else:
        if "津波の心配はありません" in text:
            return EarthquakeDomesticTsunamiEnum.No
        if "若干の海面変動" in text:
            return EarthquakeDomesticTsunamiEnum.NonEffective
        if "津波注意報" in text or "津波警報" in text and "発表" in text:
            return EarthquakeDomesticTsunamiEnum.Warning

    logger.error(f"No valid tsunami message found: text {text} and code {code}")
    return EarthquakeDomesticTsunamiEnum.No


def _foreign_tsunami(model: JMADestinationModel | JMAIntDestModel) \
        -> EarthquakeForeignTsunamiEnum:
    """Determines whether there was a tsunami or not."""
    if not model.body.comments.forecast_comment:
        logger.error("Not cancelled but no forecast_comment")
        return EarthquakeForeignTsunamiEnum.Unknown
    code = model.body.comments.forecast_comment.code
    text = model.body.comments.forecast_comment.text
    if "0215" in code:
        return EarthquakeForeignTsunamiEnum.No
    if "0221" in code:
        return EarthquakeForeignTsunamiEnum.WarningPacificWide
    if "0222" in code:
        return EarthquakeForeignTsunamiEnum.WarningPacific
    if "0223" in code:
        return EarthquakeForeignTsunamiEnum.WarningNorthwestPacific
    if "0224" in code:
        return EarthquakeForeignTsunamiEnum.WarningIndianWide
    if "0225" in code:
        return EarthquakeForeignTsunamiEnum.WarningIndian
    if "0226" in code:
        return EarthquakeForeignTsunamiEnum.WarningNearby
    if "0227" in code:
        return EarthquakeForeignTsunamiEnum.NonEffectiveNearby
    if "0228" in code:
        return EarthquakeForeignTsunamiEnum.Potential

    logger.error(f"Falling back to string parsing: got code {code}")
    if "この地震による津波の心配はありません" in text:
        return EarthquakeForeignTsunamiEnum.No

    logger.error(f"No valid tsunami message found: text {text} and code {code}")
    return EarthquakeForeignTsunamiEnum.No
