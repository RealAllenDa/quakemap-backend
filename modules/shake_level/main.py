import random

from loguru import logger

from env import Env
from model.sdk import ResponseTypeModel, ResponseTypes
from model.shake_level import ShakeLevelReturnModel, ShakeLevelApiModel
from modules.base_module import BaseModule
from sdk import func_timer, web_request, verify_none


class ShakeLevel(BaseModule):
    """
    Shake Level module.
    """

    @func_timer
    def get_info(self) -> None:
        """
        Gets shake level and green/yellow/red points info from kmoni.
        """
        if not Env.config.debug.shake_level.enabled:
            response = web_request(url="https://kwatch-24h.net/EQLevel.json",
                                   response_type=ResponseTypeModel(
                                       type=ResponseTypes.json_to_model,
                                       model=ShakeLevelReturnModel
                                   ),
                                   proxy=Env.config.proxy)
            verify_none(response.status)
            self.parse_info(response.content)
        else:
            self.parse_info(ShakeLevelReturnModel(
                status=0,
                shake_level=random.randint(50, 8000),
                green=random.randint(100, 300),
                yellow=random.randint(100, 300),
                red=random.randint(100, 300),
                sync_time="11:45"
            ))

    def parse_info(self, content: ShakeLevelReturnModel) -> None:
        """
        Parses kmoni shake level info.

        :param content: The parsed ShakeLevelApiModel
        """
        self.info = ShakeLevelApiModel(
            status=0,
            shake_level=content.shake_level,
            green=content.green,
            yellow=content.yellow,
            red=content.red
        )
        logger.info("Refreshed shake_level info.")
