from loguru import logger

from model.eew import EEWParseReturnModel, EEWReturnModel, EEWAlertTypeEnum
from model.intensity2color import AreaIntensityModel

__all__ = ["EEWInfoMiddleWare"]


class EEWInfoMiddleWare:
    @classmethod
    def combine_intensity_areas(cls, svir_info: EEWParseReturnModel, kmoni_info: EEWParseReturnModel) \
            -> dict[str, AreaIntensityModel]:
        """
        Combines the intensity areas with both info.
        :param svir_info: A EEW Info (SVIR)
        :param kmoni_info: A EEW Info (Kmoni)
        :return: Combined area_intensity Info
        """
        combined_areas = svir_info.area_coloring.areas
        if (svir_info.report_id != kmoni_info.report_id) or \
                (int(svir_info.report_num) != int(kmoni_info.report_num)):
            logger.debug("Different EEW between kmoni and svir. Returning only svir.")
            return combined_areas
        try:
            for i in kmoni_info.area_coloring.areas.keys():
                if i not in combined_areas:
                    combined_areas[i] = kmoni_info.area_coloring.areas[i]
            return combined_areas
        except Exception:
            return combined_areas

    @classmethod
    def use_svir_or_kmoni(cls, eew_info: EEWReturnModel) -> EEWParseReturnModel | dict:
        """
        Determines whether to use kmoni EEW or svir EEW.
        :param eew_info: EEW model containing svir + kmoni info
        :return: An EEW
        """
        if eew_info is None:
            logger.warning("Shouldn't happen: eew_info is None.")
            return {}

        svir_info = eew_info.svir
        kmoni_info = eew_info.kmoni

        svir_on = svir_info is not None
        kmoni_on = kmoni_info is not None

        from env import Env
        if Env.config.eew.only_dmdata:
            if svir_on:
                logger.trace("Use svir info because specified only_dmdata in config.")
                return svir_info
            else:
                logger.trace("Svir info is not avail.")
                return {}

        if (not svir_on) and (not kmoni_on):
            logger.trace(f"Return blank dict because kmoni and svir info is not available.")
            return {}
        elif (not svir_on) and kmoni_on:
            logger.debug(f"Use kmoni info because svir info is not available.")
            return kmoni_info
        elif svir_on and (not kmoni_on):
            logger.debug(f"Use svir info because kmoni info is not available.")
            return svir_info
        elif svir_on and kmoni_on:
            try:
                if svir_info.is_plum:
                    logger.debug(f"Use svir info because EEW is plum.")
                    return svir_info
                elif int(svir_info.hypocenter.depth[:-2]) >= 150:
                    logger.debug(f"Use svir info because EEW is a deep earthquake.")
                    return svir_info
                else:
                    if svir_info.report_flag == EEWAlertTypeEnum.warning:
                        svir_info.area_coloring.areas = cls.combine_intensity_areas(
                            svir_info, kmoni_info
                        )
                        logger.debug(f"Use svir info because EEW is warning.")
                        return svir_info
                    else:
                        logger.debug(f"Use kmoni info because no other conditions have been met.")
                        return kmoni_info
            except Exception as e:
                logger.exception(f"Use kmoni info because exception occurred: {e}")
                return kmoni_info
