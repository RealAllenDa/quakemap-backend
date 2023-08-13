from typing import List

from loguru import logger

from env import Env
from model.global_earthquake import CEICApiModel, GlobalEarthquakeReturnModel, EpicenterModel
from model.sdk import ResponseTypes, ResponseTypeModel
from modules.base_module import BaseModule
from sdk import func_timer, todo, web_request, verify_none


class GlobalEarthquake(BaseModule):
    """
    Global earthquake module.
    """

    def reload(self):
        self.info = None

    @func_timer
    def get_info(self) -> None:
        """
        Gets CEIC's latest earthquake telegram.
        """
        if not Env.config.debug.global_earthquake.enabled:
            response = web_request(url="https://www.ceic.ac.cn/ajax/google",
                                   response_type=ResponseTypeModel(
                                       type=ResponseTypes.json_to_list_of_models,
                                       model=CEICApiModel
                                   ),
                                   proxy=Env.config.proxy,
                                   cacheless=True,
                                   verify=False)
            verify_none(response.status)
            self.parse_info(response.content)
        else:
            todo()

    def parse_info(self, content: List[CEICApiModel]) -> None:
        """
        Parses CEIC's latest earthquake telegram.

        :param content: The list of CEIC information
        """
        self.info = []
        content_length = Env.config.global_earthquake.list_count * -1
        content = content[content_length:]
        for i in reversed(content):
            try:
                epicenter_modeled = EpicenterModel(
                    name=i.location_c,
                    depth=str(i.depth),
                    latitude=float(i.latitude),
                    longitude=float(i.longitude)
                )
                self.info.append(GlobalEarthquakeReturnModel(
                    epicenter=epicenter_modeled,
                    magnitude=i.m,
                    mmi=self._m_to_mmi(float(i.m)),
                    occur_time=i.o_time,
                    receive_time=i.sync_time
                ))
            except Exception:
                logger.exception("Failed to parse CEIC info.")
        logger.info("Refreshed global_earthquake info.")

    def _m_to_mmi(self, m: float) -> int:
        """
        Converts Richter scale to Mercalli scale.
        :param m: Richter magnitude
        :return: Mercalli magnitude
        """
        if m < 3.5:
            return 1
        elif 3.5 <= m < 4.2:
            return 2
        elif 4.2 <= m < 4.5:
            return 3
        elif 4.5 <= m < 4.8:
            return 4
        elif 4.8 <= m < 5.4:
            return 5
        elif 5.4 <= m < 6.1:
            return 6
        elif 6.1 <= m < 6.5:
            return 7
        elif 6.5 <= m < 6.9:
            return 8
        elif 6.9 <= m < 7.3:
            return 9
        elif m >= 7.3:
            return 10
