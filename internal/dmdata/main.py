import base64
import functools
import gzip
import io
import json
import os
import sys
import threading
import time
from typing import Callable, Optional

import sentry_sdk
import websocket
import xmltodict
from loguru import logger

from internal.dmdata.db import store_message_middleware
from internal.dmdata.earthquake import parse_earthquake
from internal.dmdata.eew import parse_eew
from internal.dmdata.webhook import post_message
from schemas.config import RunEnvironment
from schemas.dmdata.auth import DmdataRefreshTokenResponseModel, DmdataRequestTokenBodyModel, \
    DmdataRefreshTokenErrorModel
from schemas.dmdata.generic import DmdataGenericErrorResponse, DmdataMessageTypes, DmdataStatusModel
from schemas.dmdata.socket import DmdataSocketStartResponse, DmdataSocketStartBody, DmdataSocketError, DmdataPing, \
    DmdataSocketStart, DmdataPong, DmdataSocketData
from schemas.p2p_info import EarthquakeReturnModel, EarthquakeIssueTypeEnum
from schemas.sdk import ResponseTypeModel, ResponseTypes, RequestTypes
from sdk import web_request, func_timer, obj_to_model


class DMDataFetcher:
    """
    Fetches DMData.

    NOTE:
        This module uses an unverified way to fetch data in order to save expense.
        This COULD be classified as ABUSE, and is extremely discouraged.
        To use this method, you must extract all the keys on your OWN.
    """

    def __init__(self):
        self.message = None
        self.shutdown = False
        self.socket_url = None
        self.active_socket_id = None
        self.websocket: Optional[websocket.WebSocketApp] = None

        from env import Env
        if Env.run_env == RunEnvironment.testing:
            logger.warning("Unit testing - skipped initialization.")
            self.testing = True
            return
        else:
            self.testing = False

        self.access_token = None

        self.pong = None
        self.last_pong_time = int(time.time())

        self.refresh_token = os.getenv("REFRESH_TOKEN")
        if self.refresh_token is None or self.refresh_token == "":
            logger.critical("Failed to initialize DMData: No REFRESH_TOKEN defined in environ.")
            sys.exit(1)

        if Env.config.dmdata.jquake.use_plan:
            self._init_jquake_config()
        else:
            logger.critical("NOT IMPLEMENTED: Non-Jquake token")
            sys.exit(1)

        self.previous_scale_prompt: Optional[EarthquakeReturnModel] = None

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

    @property
    def status(self) -> DmdataStatusModel:
        """Dmdata status.
        """
        pong_time_delta = int(time.time()) - self.last_pong_time
        if self.websocket:
            websocket_errored = self.websocket.has_errored
        else:
            websocket_errored = True
        status = (self.active_socket_id is not None and not self.websocket.has_errored and pong_time_delta < 1800)
        return DmdataStatusModel(
            status="OK" if status else "FAIL",
            active_socket_id=str(self.active_socket_id),
            websocket_errored=websocket_errored,
            last_pong_time=self.last_pong_time,
            pong_time_delta=pong_time_delta
        )

    def start_connection(self):
        """
        Starts Dmdata connection.
        """
        if self.shutdown:
            logger.trace("Shutdown - no websocket needed.")
            return
        logger.debug("Trying to start a connection...")
        if self.websocket:
            # Active websocket
            return
        with sentry_sdk.start_transaction(op="start_dmdata", name="start_connection", sampled=True):
            with sentry_sdk.start_span(op="get_socket"):
                self.get_socket()
            with sentry_sdk.start_span(op="connect_socket"):
                self.connect_socket()

    def keep_alive(self):
        """
        Check whether the socket was alive.

        Runs every 1 minute.
        """
        if (not self.websocket) or \
                self.websocket.has_errored or \
                (not self.active_socket_id):
            logger.warning("No active websocket available! Starting a new one.")
        elif int(time.time()) - self.last_pong_time > 1800:
            logger.error(f"Last pong too long! (span={int(time.time()) - self.last_pong_time})")
        else:
            logger.debug("Socket is alive!")
            return
        tries = 0
        while (not self.websocket) and (tries < 2):
            self.get_current_token()
            self.start_connection()
            time.sleep(10)
            tries += 1
        if not self.active_socket_id:
            # Still not websocket.
            logger.error("Still no active websocket available! Check logs.")

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
        ).model_dump()
        response = web_request(
            url="https://manager.dmdata.jp/account/oauth2/v1/token",
            response_type=ResponseTypeModel(
                type=ResponseTypes.json_to_multiple_model,
                model=[DmdataRefreshTokenResponseModel, DmdataRefreshTokenErrorModel]
            ),
            max_retries=1,
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
                "VXSE45"
            ],
            appName="JQuake-1.8.5"
        ).model_dump_json(by_alias=True)
        response = web_request(
            url=f"https://api.dmdata.jp/v2/socket",
            response_type=ResponseTypeModel(
                type=ResponseTypes.json_to_multiple_model,
                model=[DmdataSocketStartResponse, DmdataGenericErrorResponse]
            ),
            request_type=RequestTypes.post,
            proxy=Env.config.proxy,
            bearer_token=self.access_token,
            form_data=form_data,
            max_retries=1
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
    def close_socket(self, tries=3):
        """
        Closes socket connection.
        """
        if self.active_socket_id is None:
            logger.warning("No active socket.")
            return
        with sentry_sdk.start_transaction(op="start_dmdata", name="close_socket", sampled=True):
            from env import Env
            web_request(
                url=f"https://api.dmdata.jp/v2/socket/{self.active_socket_id}",
                response_type=ResponseTypeModel(
                    type=ResponseTypes.raw_response
                ),
                request_type=RequestTypes.delete,
                proxy=Env.config.proxy,
                bearer_token=self.access_token,
                max_retries=tries
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
        if message.code == 4808:
            logger.warning("DMData socket closed. If this is not during shutdown, "
                           "something bad has happened.")
            return
        logger.error(f"DMData socket error: "
                     f"code => {message.code}, error => {message.error}, closed => {message.close}")
        if message.close:
            self.close_socket()
            self.start_connection()

    def parse_ping_message(self, message: Optional[DmdataPing]):
        """
        Parses Dmdata ping message.

        :param message: Dmdata ping message
        """
        if not message:
            logger.error("Failed to parse ping message: message is None")
            return
        self.pong = DmdataPong(
            pingId=message.ping_id
        ).model_dump_json(by_alias=True)
        logger.debug(f"Sending pong: {self.pong}")
        self.websocket.send(self.pong)
        self.last_pong_time = int(time.time())

    @func_timer(log_func=logger.success)
    def parse_data_message(self, message: Optional[DmdataSocketData]) -> int:
        """
        Parses Dmdata data message.

        :param message: Dmdata data message
        """
        if not message:
            logger.error("Failed to parse data message: message is None")
            return 1

        logger.trace(f"Parsed message: {message}")
        # with open(relpath(f"../data/{message.id}.json"), "w+", encoding="utf-8") as f:
        #     f.write(message.json())
        #     f.close()

        if message.format != "xml":
            logger.error("Failed to parse data message: format is not XML")
            return 1
        if message.compression != "gzip" or message.encoding != "base64":
            logger.error("Failed to parse data message: Data compression is not gzip/Encoding is not base64")
            return 1
        if message.xmlReport is None:
            logger.error("Suspicious message: format is XML but no xmlReport")

        try:
            raw_io = io.BytesIO(base64.b64decode(message.body))
            raw_message = gzip.decompress(raw_io.read())
            raw_message = raw_message.decode("utf-8")
            xml_message = xmltodict.parse(raw_message, encoding="utf-8")
            raw_io.close()
        except Exception:
            logger.exception("Failed to parse data message.")
            return 1

        hooks = [
            threading.Thread(target=store_message_middleware, args=(message, xml_message),
                             daemon=True),
            threading.Thread(target=post_message, args=(message.body,),
                             daemon=True)
        ]
        self.message = message.body
        for t in hooks:
            t.start()

        from internal.modules_init import module_manager
        if message.head.type == DmdataMessageTypes.eew_warning \
                or message.head.type == DmdataMessageTypes.eew_forecast:
            # EEW
            if self.testing:
                print(xml_message)
            with sentry_sdk.start_span(op="transform_eew"):
                eew = parse_eew(xml_message, message.head.type)
            if self.testing:
                print(eew)
            if eew is None:
                logger.error("Failed to parse Dmdata EEW: is None")
                return 1
            try:
                with sentry_sdk.start_span(op="parse_eew"):
                    module_manager.classes["eew_info"].parse_iedred_eew(eew)
            except Exception:
                logger.exception("Failed to parse Dmdata EEW.")
                return 1
        if message.head.type == DmdataMessageTypes.tsunami_info \
                or message.head.type == DmdataMessageTypes.tsunami_warning:
            # tsunami
            if self.testing:
                print(xml_message)
            try:
                with sentry_sdk.start_span(op="parse_tsunami"):
                    module_manager.classes["tsunami"].parse_dmdata(xml_message, message.head.type)
            except Exception:
                logger.exception("Failed to parse Dmdata tsunami.")
                return 1
        if message.head.type == DmdataMessageTypes.eq_intensity_report \
                or message.head.type == DmdataMessageTypes.eq_destination \
                or message.head.type == DmdataMessageTypes.eq_intensity_destination:
            # or message.head.type == DmdataMessageTypes.eq_destination_change:
            # eq_destination_change fixme
            with sentry_sdk.start_span(op="transform_earthquake"):
                info = parse_earthquake(xml_message, message.head.type)
            if info == "None":
                logger.error("Failed to parse Dmdata earthquake: is None")
                return 1
            try:
                # If info's type is Destination, we do not purge the list
                # to ensure that scale and destination could appear in the same page.
                with sentry_sdk.start_span(op="parse_earthquake"):
                    if info == "Cancel":
                        module_manager.classes["p2p_info"].cancel_earthquake_info()
                    else:
                        prev_eq_info: list[EarthquakeReturnModel] = module_manager.classes[
                            "p2p_info"].get_earthquake_info()
                        if info.type == EarthquakeIssueTypeEnum.ScalePrompt:
                            self.previous_scale_prompt = info
                        if info.type == EarthquakeIssueTypeEnum.Destination:
                            if prev_eq_info[0].type == EarthquakeIssueTypeEnum.ScalePrompt:
                                module_manager.classes["p2p_info"].set_earthquake_info([prev_eq_info[0], info])
                            else:
                                logger.warning(
                                    f"Rare case where Destination is not after ScalePrompt: {prev_eq_info[0].type}")
                                # fallback to previous scale prompt
                                if self.previous_scale_prompt is None:
                                    assert False, "No previous scale prompt available."
                                if self.previous_scale_prompt.id != info.id:
                                    assert False, "Previous scale prompt id != current id."
                                module_manager.classes["p2p_info"].set_earthquake_info(
                                    [self.previous_scale_prompt, info])
                        else:
                            self.previous_scale_prompt = None
                            module_manager.classes["p2p_info"].set_earthquake_info([info])
            except Exception:
                logger.exception("Failed to parse Dmdata earthquake.")
                return 1

        for t in hooks:
            t.join(5)
        return 0

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
        if status_code == "4808" or status_code is None:
            return
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
            with sentry_sdk.start_transaction(op="parse_dmdata", name="start"):
                self.parse_start_message(message)
        elif message_type == "ping":
            message = obj_to_model(message, DmdataPing)
            with sentry_sdk.start_transaction(op="parse_dmdata", name="ping"):
                self.parse_ping_message(message)
        elif message_type == "data":
            message = obj_to_model(message, DmdataSocketData)
            with sentry_sdk.start_transaction(op="parse_dmdata", name="data", sampled=True):
                self.parse_data_message(message)
        elif message_type == "error":
            message = obj_to_model(message, DmdataSocketError)
            with sentry_sdk.start_transaction(op="parse_dmdata", name="error", sampled=True):
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
        if self.socket_url is None:
            logger.warning("self.socket_url is None. Check get_socket() status.")
            return
        logger.debug(f"Connecting to {self.socket_url}")
        if self.websocket:
            logger.warning("self.websocket is not None. Probably another socket opened.")
            return

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
        self.shutdown = True
        self.websocket.close()
        self.close_socket(0)
        self.websocket = True
        self.websocket.has_errored = False
