#  CONFIDENTIAL HomeNetwork
#  Unpublished Copyright (c) 2023.
#
#  NOTICE: All information contained herein is, and remains the property of HomeNetwork.
#  Dissemination of this information or reproduction of this material is strictly forbidden unless
#  prior written permission is obtained from HomeNetwork.

import base64
import functools
import gzip
import io
import json
import os
import re
import sys
import time
from typing import Callable, Optional

import sentry_sdk
import websocket
import xmltodict
from loguru import logger

from model.dmdata.auth import DmdataRefreshTokenResponseModel, DmdataRequestTokenBodyModel, DmdataRefreshTokenErrorModel
from model.dmdata.generic import DmdataGenericErrorResponse, DmdataMessageTypes
from model.dmdata.socket import DmdataSocketStartResponse, DmdataSocketStartBody, DmdataSocketError, DmdataPing, \
    DmdataSocketStart, DmdataPong, DmdataSocketData
from model.eew import IedredEEWModel, IedredParseStatus, IedredEventType, SvirEventType, IedredEventTypeEnum, \
    IedredCodeStringDetail, IedredTime, IedredHypocenter, IedredLocation, IedredEpicenterDepth, IedredMagnitude, \
    IedredMaxIntensity, EEWIntensityEnum, IedredForecastAreasArrival, IedredForecastAreas, IedredForecastAreasIntensity
from model.jma.eew import JMAEEWApiModel
from model.jma.tsunami_expectation import JMAInfoType, JMAControlStatus
from model.sdk import ResponseTypeModel, ResponseTypes, RequestTypes
from sdk import web_request, func_timer, obj_to_model, generate_list


class DMDataFetcher:
    """
    Fetches DMData.

    NOTE:
        This module uses an unverified way to fetch data in order to save expense.
        This COULD be classified as ABUSE, and is extremely discouraged.
        To use this method, you must extract all the keys on your OWN.
    """

    def __init__(self, testing=False):
        self.testing = testing
        if testing:
            print("Unit testing - skipped initialization")
            return
        self.socket_url = None
        self.active_socket_id = None
        self.websocket: Optional[websocket.WebSocketApp] = None

        self.access_token = None

        self.pong = None

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
        logger.debug("Trying to start a connection...")
        if self.websocket:
            # Active websocket
            return
        with sentry_sdk.start_transaction(op="start_dmdata", name="start_connection"):
            self.get_socket()
            self.connect_socket()

    def keep_alive(self):
        """
        Check whether the socket was alive.

        Runs every 1 minute.
        """
        if not self.websocket:
            logger.warning("No active websocket available! Starting a new one.")
        else:
            logger.debug("Socket is alive!")
            return
        tries = 0
        while (not self.websocket) and (tries < 2):
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
    def close_socket(self):
        """
        Closes socket connection.
        """
        if self.active_socket_id is None:
            logger.warning("No active socket.")
            return
        with sentry_sdk.start_transaction(op="start_dmdata", name="close_socket"):
            from env import Env
            web_request(
                url=f"https://api.dmdata.jp/v2/socket/{self.active_socket_id}",
                response_type=ResponseTypeModel(
                    type=ResponseTypes.raw_response
                ),
                request_type=RequestTypes.delete,
                proxy=Env.config.proxy,
                bearer_token=self.access_token,
                max_retries=3
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
        if message.code == 4640:
            # PingId verification failed - not receiving pong?
            if self.pong is None:
                logger.error("Receiving ping error, however pong is not created. "
                             "Perhaps error with message transmission? ")
            else:
                logger.debug("Sending pong again...")
                self.websocket.send(self.pong)

    def parse_ping_message(self, message: Optional[DmdataPing]):
        """
        Parses Dmdata ping message.

        :param message: Dmdata ping message
        """
        if not message:
            logger.error("Failed to parse ping message: message is None")
            return
        self.pong = DmdataPong(
            ping_id=message.ping_id
        ).json(by_alias=True)
        logger.debug(f"Sending pong: {self.pong}")
        self.websocket.send(self.pong)

    @func_timer(log_func=logger.success)
    def parse_data_message(self, message: Optional[DmdataSocketData]):
        """
        Parses Dmdata data message.

        :param message: Dmdata data message
        """
        if not message:
            logger.error("Failed to parse data message: message is None")
            return

        logger.trace(f"Parsed message: {message}")
        # with open(relpath(f"../data/{message.id}.json"), "w+", encoding="utf-8") as f:
        #     f.write(message.json())
        #     f.close()

        if message.format != "xml":
            logger.error("Failed to parse data message: format is not XML")
            return
        if message.compression != "gzip" or message.encoding != "base64":
            logger.error("Failed to parse data message: Data compression is not gzip/Encoding is not base64")
            return

        try:
            raw_io = io.BytesIO(base64.b64decode(message.body))
            raw_message = gzip.decompress(raw_io.read())
            raw_message = raw_message.decode("utf-8")
            xml_message = xmltodict.parse(raw_message, encoding="utf-8")
            raw_io.close()
        except Exception:
            logger.exception("Failed to parse data message.")
            return

        from internal.modules_init import module_manager
        if message.head.type == DmdataMessageTypes.eew_warning \
                or message.head.type == DmdataMessageTypes.eew_forecast:
            # EEW
            if self.testing:
                print(xml_message)
            eew = self.parse_eew(xml_message)
            if self.testing:
                print(eew)
            if eew is None:
                logger.error("Failed to parse Dmdata EEW: is None")
                return
            try:
                module_manager.classes["eew_info"].parse_iedred_eew(eew)
            except Exception:
                logger.exception("Failed to parse Dmdata EEW.")
        # tsunami, earthquake todo

    @func_timer(log_func=logger.debug)
    def parse_eew(self, content: dict) -> Optional[IedredEEWModel]:
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
        origin_time = report.body.earthquake.origin_time.timetuple()

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
        is_warn = report.head.title == "緊急地震速報（警報）"

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
        else:
            lowest_intensity = EEWIntensityEnum.no

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
            is_warn=is_warn
        )

        if return_model.is_warn and (report.body.intensity.forecast.areas is not None):
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
                return_model.forecast_areas.append(IedredForecastAreas(
                    intensity=IedredForecastAreasIntensity(
                        code=i.area.code,
                        name=i.area.name,
                        lowest=EEWIntensityEnum[i.area.forecast_intensity.lowest.name],
                        highest=EEWIntensityEnum[i.area.forecast_intensity.highest.name],
                        description=str(i.area.forecast_intensity.lowest.name)
                    ),
                    is_warn=(i.area.forecast_kind.kind.name == "緊急地震速報（警報）"),
                    has_arrived=arrival_time
                ))

        return return_model

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
            with sentry_sdk.start_transaction(op="parse_dmdata", name="start"):
                self.parse_start_message(message)
        elif message_type == "ping":
            message = obj_to_model(message, DmdataPing)
            with sentry_sdk.start_transaction(op="parse_dmdata", name="ping"):
                self.parse_ping_message(message)
        elif message_type == "data":
            message = obj_to_model(message, DmdataSocketData)
            with sentry_sdk.start_transaction(op="parse_dmdata", name="data"):
                self.parse_data_message(message)
        elif message_type == "error":
            message = obj_to_model(message, DmdataSocketError)
            with sentry_sdk.start_transaction(op="parse_dmdata", name="error"):
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
        self.close_socket()
