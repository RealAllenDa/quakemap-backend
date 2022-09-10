#  CONFIDENTIAL HomeNetwork
#  Unpublished Copyright (c) 2022.
#
#  NOTICE: All information contained herein is, and remains the property of HomeNetwork.
#  Dissemination of this information or reproduction of this material is strictly forbidden unless
#  prior written permission is obtained from HomeNetwork.
import functools
import json
import os
import sys
from typing import Callable, Optional

import websocket
from loguru import logger

from model.dmdata.auth import DmdataRefreshTokenResponseModel, DmdataRequestTokenBodyModel, DmdataRefreshTokenErrorModel
from model.dmdata.generic import DmdataGenericErrorResponse
from model.dmdata.socket import DmdataSocketStartResponse, DmdataSocketStartBody, DmdataSocketError, DmdataPing, \
    DmdataSocketStart, DmdataPong, DmdataSocketData
from model.sdk import ResponseTypeModel, ResponseTypes, RequestTypes
from sdk import web_request, func_timer, obj_to_model, relpath


class DMDataFetcher:
    """
    Fetches DMData.

    NOTE:
        This module uses an unverified way to fetch data in order to save expense.
        This COULD be classified as ABUSE, and is extremely discouraged.
        To use this method, you must extract all the keys on your OWN.
    """

    def __init__(self):
        self.socket_url = None
        self.active_socket_id = None
        self.websocket: Optional[websocket.WebSocketApp] = None

        self.access_token = None

        self.refresh_token = os.getenv("REFRESH_TOKEN")
        if self.refresh_token is None or self.refresh_token == "":
            logger.critical("Failed to initialize DMData: No REFRESH_TOKEN defined in environ.")
            sys.exit(1)

        from env import Env
        if Env.config.dmdata.jquake.use_plan:
            self._init_jquake_config()
        else:
            logger.critical("NOT IMPLEMENTED: Non-Jquake token")
            sys.exit(1)

        logger.success("DMData instance initialized.")

    def _init_jquake_config(self):
        """
        Initializes JQuake-specialized config.
        """
        from env import Env
        self.client_id = Env.config.dmdata.jquake.client_id
        self.client_token = Env.config.dmdata.jquake.client_token
        if self.client_id == "" or self.client_token == "":
            logger.critical("Failed to initialize DMData: No client_id and client_token specified.")
            sys.exit(1)
        self.get_current_token()

    def start_connection(self):
        """
        Starts Dmdata connection.
        """
        if self.websocket:
            # Active websocket
            return
        self.get_socket()
        self.connect_socket()

    @func_timer
    def get_current_token(self) -> None:
        """
        Gets current access token using refresh token.
        """
        from env import Env
        form_data = DmdataRequestTokenBodyModel(
            client_id=self.client_id,
            client_secret=self.client_token,
            refresh_token=self.refresh_token
        ).dict()
        response = web_request(
            url="https://manager.dmdata.jp/account/oauth2/v1/token",
            response_type=ResponseTypeModel(
                type=ResponseTypes.json_to_multiple_model,
                model=[DmdataRefreshTokenResponseModel, DmdataRefreshTokenErrorModel]
            ),
            request_type=RequestTypes.post,
            form_data=form_data,
            proxy=Env.config.proxy
        )
        if not response.status:
            logger.error("Failed to refresh DMData token.")
            return

        content = response.content
        if isinstance(response.content, DmdataRefreshTokenErrorModel):
            content: DmdataRefreshTokenErrorModel
            logger.error(f"Failed to refresh DMData token: {content.error.value} => {content.error_description}")
            return

        content: DmdataRefreshTokenResponseModel
        self.access_token = content.access_token
        logger.info(f"Successfully got DMData access token: {self.access_token[:5]}***")
        logger.debug(f"Access token: {self.access_token}")

    @func_timer
    def get_socket(self):
        """
        Gets socket endpoint using access token.
        """
        self.socket_url = None

        from env import Env
        # NOTE: JSON!
        form_data = DmdataSocketStartBody(
            classifications=[
                "application.jquake",
                "telegram.earthquake",
                "eew.forecast"
            ],
            types=[
                "VXSE51",
                "VXSE52",
                "VXSE53",
                "VXSE61",
                "VTSE41",
                "VTSE51",
                "VXSE43",
                "VXSE44"
            ],
            app_name="JQuake"
        ).json(by_alias=True)
        response = web_request(
            url=f"https://api.dmdata.jp/v2/socket",
            response_type=ResponseTypeModel(
                type=ResponseTypes.json_to_multiple_model,
                model=[DmdataSocketStartResponse, DmdataGenericErrorResponse]
            ),
            request_type=RequestTypes.post,
            proxy=Env.config.proxy,
            bearer_token=self.access_token,
            form_data=form_data
        )
        if not response.status:
            logger.error("Failed to get DMData socket endpoint.")
            return

        content = response.content
        if isinstance(response.content, DmdataGenericErrorResponse):
            content: DmdataGenericErrorResponse
            logger.error(f"Failed to get DMData socket endpoint: {content.error.code} => {content.error.message}")
            return

        content: DmdataSocketStartResponse
        self.socket_url = content.websocket.url
        self.active_socket_id = content.websocket.id
        logger.info(f"Successfully got DMData socket endpoint: {self.active_socket_id}")
        logger.debug(f"Ticket: {content.ticket}. Url: {content.websocket.url}")

    @func_timer
    def close_socket(self):
        """
        Closes socket connection.
        """
        if self.active_socket_id is None:
            logger.warning("No active socket.")
            return

        from env import Env
        web_request(
            url=f"https://api.dmdata.jp/v2/socket/{self.active_socket_id}",
            response_type=ResponseTypeModel(
                type=ResponseTypes.raw_response
            ),
            request_type=RequestTypes.delete,
            proxy=Env.config.proxy,
            bearer_token=self.access_token,
            max_retries=1
        )

        self.socket_url = None
        self.websocket = None
        self.active_socket_id = None

        logger.success("Successfully closed socket.")

    def parse_start_message(self, message: Optional[DmdataSocketStart]):
        """
        Parses Dmdata start message.

        :param message: Dmdata start message
        """
        if not message:
            logger.error("Failed to parse start message: message is None")
            return
        logger.success("Successfully connected with DMData! "
                       f"Id => {message.socket_id}, time => {message.time}")

    def parse_error_message(self, message: Optional[DmdataSocketError]):
        """
        Parses Dmdata error message.

        :param message: Dmdata error message
        """
        if not message:
            logger.error("Failed to parse error message: message is None")
            return
        logger.warning(f"DMData socket error: "
                       f"code => {message.code}, error => {message.error}, closed => {message.close}")

    def parse_ping_message(self, message: Optional[DmdataPing]):
        """
        Parses Dmdata ping message.

        :param message: Dmdata ping message
        """
        if not message:
            logger.error("Failed to parse ping message: message is None")
            return
        pong = DmdataPong(
            ping_id=message.ping_id
        ).json(by_alias=True)
        logger.debug(f"Sending pong: {pong}")
        self.websocket.send(pong)

    @func_timer
    def parse_data_message(self, message: Optional[DmdataSocketData]):
        """
        Parses Dmdata data message.

        :param message: Dmdata data message
        """
        if not message:
            logger.error("Failed to parse data message: message is None")
            return
        print(message)
        with open(relpath(f"../data/{message.id}.json"), "w+", encoding="utf-8") as f:
            f.write(message.json())
            f.close()

    def _ws_func_wrapper(self, func: Callable[..., None]):
        """
        Wraps websocket function with class globals.

        :param func: The function to wrap
        :return: Wrapped function
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            return value

        return wrapper

    def _ws_open(self, _):
        """
        Websocket onopen
        """
        logger.info(f"Successfully established DMData websocket connection. "
                    f"Id => {self.active_socket_id}")

    def _ws_close(self, _, status_code: str, message: str):
        """
        Websocket onclose

        :param status_code: The close status code
        :param message: The close message
        """
        logger.warning(f"Websocket closed! Status: {status_code}, message: {message}")
        self.close_socket()
        self.start_connection()

    def _ws_onmessage(self, _, message: str):
        """
        Websocket onmessage
        """
        logger.debug(f"Message: {message}")

        try:
            message = json.loads(message)
        except Exception:
            logger.exception("Failed to parse message to JSON.")
            return

        message_type = message["type"]
        if message_type == "start":
            message = obj_to_model(message, DmdataSocketStart)
            self.parse_start_message(message)
        elif message_type == "ping":
            message = obj_to_model(message, DmdataPing)
            self.parse_ping_message(message)
        elif message_type == "data":
            message = obj_to_model(message, DmdataSocketData)
            self.parse_data_message(message)
        elif message_type == "error":
            message = obj_to_model(message, DmdataSocketError)
            self.parse_error_message(message)
        else:
            logger.error(f"Exhaustive handling of message_type: {message_type}. Message => {message}")

    def _ws_onerror(self, _, error):
        """
        Websocket onerror
        """
        logger.error(f"Websocket errored! Error: {error}")
        self.close_socket()
        self.start_connection()

    @func_timer
    def connect_socket(self):
        """
        Connects to the socket.
        """
        logger.debug(f"Connecting to {self.socket_url}")
        if self.websocket:
            logger.warning("self.websocket is not None. Probably another socket opened.")

        self.websocket = websocket.WebSocketApp(
            self.socket_url,
            on_open=self._ws_func_wrapper(self._ws_open),
            on_message=self._ws_func_wrapper(self._ws_onmessage),
            on_error=self._ws_func_wrapper(self._ws_onerror),
            on_close=self._ws_func_wrapper(self._ws_close)
        )
        self.websocket.run_forever()

    @func_timer
    def cleanup(self):
        """
        Cleans up.
        """
        self.close_socket()
