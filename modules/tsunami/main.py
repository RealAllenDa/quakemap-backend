from devtools import pprint

from env import Env
from model.jma import JMAList
from model.sdk import ResponseTypeModel, ResponseTypes
from modules.base_module import BaseModule
from sdk import func_timer, web_request, verify_none


class TsunamiInfo(BaseModule):
    """
    Tsunami Info module.
    """

    @func_timer
    def get_info(self) -> None:
        """
        Gets JMA's information list XML. (eqvol.xml)
        """
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
        pprint(content)
