"""
 HomeNetwork Python SDK
 Licensed under GPL.
 2022-2023 Allen Da.
 Current Version - 1.1
"""
__all__ = [
    # Formation conversion
    "yaml_to_model", "json_to_model", "obj_to_model",
    # File operation
    "read_csv", "read_json", "open_file",
    # API operation
    "web_request",
    # Misc operation
    "relpath", "func_timer", "parse_jsonp", "generate_list",
    # Assert operation
    "todo", "verify_none", "verify_not_used", "verify_type"
]

import csv
import functools
import json
import re
import time
import types
from typing import TypeVar, Type, Optional, Callable, TextIO, Any, Tuple, List, Union

import requests
import xmltodict
import yaml
from loguru import logger
from pydantic import BaseModel
from requests import ReadTimeout, Response

from model.config import ProxyConfigModel
from model.sdk import ResponseTypeModel, ResponseModel, ResponseTypes, RequestTypes

OnlyModel = TypeVar("OnlyModel", bound=Type[BaseModel])
T = TypeVar("T")


class VerifyFailedException(Exception):
    """
    Exception to indicate that verify failed.
    """

    def __init__(self, message="Unknown error"):
        super().__init__(f"VERIFY failed: {message}.")


def _raise_verify_exception(message: str) -> None:
    """
    Raises verify failed exception.
    Shall not be used externally.

    :param message: The verify failed message
    """
    try:
        raise VerifyFailedException(message)
    except Exception as e:
        logger.exception("VERIFY failed.")
        raise e


def todo() -> None:
    """
    Indicates that the function is not finished.
    """
    _raise_verify_exception("todo!")


def verify_none(variable: Any) -> None:
    """
    Verifies whether the variable is none.

    :param variable: The variable
    """
    if not variable:
        _raise_verify_exception("Variable is none or false")


def verify_not_used(name: str, use_type: str = "declaration") -> None:
    """
    Indicates that the code shouldn't be reached.

    :param name: The function/variable/code name
    :param use_type: The use type of the function/variable/code
    """
    _raise_verify_exception(f"Use before {use_type}: {name}")


def verify_type(
        instance: object,
        instance_type: type | types.UnionType | Tuple[type | types.UnionType | Tuple[Any, ...], ...]
) -> None:
    """
    Verifies whether the instance is the chosen type.

    :param instance: The instance itself
    :param instance_type: The type
    """
    if not isinstance(instance, instance_type):
        try:
            raise VerifyFailedException(f"Type mismatch: {instance} is {type(instance)}, "
                                        f"which should be {instance_type}")
        except Exception as e:
            logger.exception("VERIFY failed.")
            raise e


def open_file(filename: str, mode: str = "r+") -> Optional[TextIO]:
    """
    Opens a file and returns the handle.

    :param filename: The file to read
    :param mode: The open mode
    :return: The file handle
    """
    try:
        handle = open(filename, mode=mode, encoding="utf-8")
    except Exception:
        logger.exception(f"Failed to open file {filename} with {mode}.")
        return None
    return handle


def yaml_to_model(filename: str, model: OnlyModel) -> Optional[OnlyModel]:
    """
    Converts a yaml file to specified model.

    :param filename: The yaml file path
    :param model: The target model
    :return: The model with data
    """
    logger.debug(f"Yaml to model: {filename} -> {model}")
    handle = open_file(filename)
    verify_none(handle)
    try:
        content = yaml.safe_load(handle)
    except Exception:
        logger.exception(f"Failed to open file {filename}.")
        return None
    finally:
        handle.close()
    parsed_content = obj_to_model(content, model)
    verify_none(parsed_content)
    return parsed_content


# noinspection PyProtectedMember
def relpath(file_path: str) -> str:
    """
    Locates to the correct relative path.

    :param file_path: The relative path
    :return: The absolute path
    """
    from sys import _getframe
    from pathlib import Path
    frame = _getframe(1)
    curr_file = Path(frame.f_code.co_filename)
    return str(curr_file.parent.joinpath(file_path).resolve())


def parse_jsonp(jsonp_str: str) -> str:
    """
    Parses the jsonp string into a json string.
    :param jsonp_str: JSONP string
    :return: JSON String
    """
    try:
        return re.search(r"^[^(]*?\((.*)\)[^)]*$", jsonp_str).group(1)
    except Exception:
        verify_not_used("JSONP", "Invalid JSONP")


def func_timer(func: Callable[..., T]) -> T:
    """
    Profiles a function's time usage.

    :param func: The called function
    :return: A function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        # noinspection PyUnresolvedReferences
        logger.debug(f"{func.__module__}:{func.__name__} => {(end_time - start_time):.3f} secs.")
        return value

    return wrapper


def read_json(filename: str, mode: str = "r+") -> Optional[dict]:
    """
    Reads Json from a file.

    :param filename: File to be loaded
    :param mode: The opening mode
    :return: A dict
    """
    logger.debug(f"Read json: {filename} with {mode}")
    handle = open_file(filename, mode=mode)
    verify_none(handle)
    try:
        content = json.load(handle)
    except Exception:
        logger.exception(f"Failed to load file {filename} into json.")
        return None
    finally:
        handle.close()
    return content


def obj_to_model(obj: object, model: OnlyModel) -> Optional[OnlyModel]:
    """
    Converts an object into a model.

    :param obj: The object
    :param model: The target model
    :return: Model with data
    """
    try:
        parsed_model = model.parse_obj(obj)
    except Exception:
        logger.exception(f"Failed to parse object {obj} -> {model}.")
        return None
    return parsed_model


def json_to_model(filename: str, model: OnlyModel) -> Optional[OnlyModel]:
    """
    Converts json file into a model.

    :param filename: The Json file path
    :param model: The target model
    :return: Model with data
    """
    logger.debug(f"Json to model: {filename} -> {model}")
    json_file = read_json(filename)
    verify_none(json_file)
    try:
        parsed_model = obj_to_model(json_file, model)
    except Exception:
        logger.exception(f"Failed to convert json {filename} -> {model}.")
        return None
    return parsed_model


def read_csv(filename: str,
             fieldnames: tuple) -> Optional[List]:
    """
    Converts csv file into a model.

    :param filename: The csv file path
    :param fieldnames: Csv fields
    :return: csv.DictReader
    """
    logger.debug(f"Read csv: {filename} with {fieldnames}")
    file = open_file(filename=filename)
    verify_none(file)
    try:
        parsed_csv = csv.DictReader(file, fieldnames=fieldnames)
        rows = [
            i for i in parsed_csv
        ]
        return rows
    except Exception:
        logger.exception(f"Failed to parse file into csv: {filename}.")
        return None
    finally:
        file.close()


def generate_list(name: T) -> list[T]:
    """
    Make sure parameter is a list.

    :param name: A dict or a list
    :return: Guaranteed to be a list
    :rtype: list
    """
    if not name:
        return []
    elif isinstance(name, list):
        return name
    else:
        return [name]


def web_request(url: str,
                response_type: ResponseTypeModel,
                max_retries: int = 3,
                timeout: Union[int, float] = 3.5,
                proxy: Optional[ProxyConfigModel] = None,
                cacheless: bool = False,
                verify: bool = True,
                headers: dict = None,
                request_type: RequestTypes = RequestTypes.get,
                form_data: dict | str = None,
                bearer_token: str = None) \
        -> ResponseModel:
    """
    Makes web request.

    :param url: The URL
    :param response_type: What should this function return
    :param max_retries: The maximum times to retry
    :param timeout: The timeout
    :param proxy: The proxy to use
    :param cacheless: Whether to ignore cache by adding seed
    :param verify: Whether to verify https certificate
    :param headers: The request header to append
    :param request_type: The request type (POSt, GET, etc.)
    :param form_data: The form data to append
    :param bearer_token: The bearer token for OAuth2 API endpoints
    :return: ResponseModel
    """
    retries = 0
    response: Optional[Response] = None
    if headers is None:
        headers = {}
    logger.debug(f"Web request with url {url} -> {response_type}, "
                 f"timeout {timeout} and cache-less {cacheless}")
    if cacheless:
        url += f"&time={int(time.time())}"
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    while retries < max_retries:
        try:
            response = requests.request(method=str(request_type.value),
                                        url=url,
                                        proxies=proxy.dict(),
                                        timeout=timeout,
                                        verify=verify,
                                        headers=headers,
                                        data=form_data)
        except ReadTimeout:
            logger.warning(
                f"Connection timed out: url {url} with timeout {timeout}. Retrying for the {retries} time(s)."
            )
            retries += 1
            time.sleep(retries * retries)
            continue
        except Exception:
            logger.exception(f"Failed to fetch. Retrying for the {retries} time(s).")
            retries += 1
            time.sleep(retries * retries)
            continue

        # --- Response verification
        if response.status_code != 200:
            logger.warning(f"Failed response verification: code: {response.status_code} != 200. "
                           f"Retrying for the {retries} time(s).")
            retries += 1
            time.sleep(retries * retries)
            continue
        elif response.text == "":
            logger.warning(f"Failed response verification: text: is none. Retrying for the {retries} time(s).")
            retries += 1
            time.sleep(retries * retries)
            continue
        else:
            # Successful
            break

    if response is None:
        logger.error("Maximum retries exceeded without succeeding.")
        return ResponseModel()
    response.encoding = "utf-8"

    # --- Response conversion
    verify_type(response_type, ResponseTypeModel)
    if response_type.type == ResponseTypes.json_to_model:
        try:
            obj = response.json()
        except Exception:
            logger.exception(f"Failed to convert response to object")
            return ResponseModel()
        verify_none(response_type.model)
        model = obj_to_model(obj, response_type.model)
        if model is not None:
            return ResponseModel(
                status=True,
                content=model
            )
        else:
            return ResponseModel()
    elif response_type.type == ResponseTypes.json_to_multiple_model:
        try:
            obj = response.json()
        except Exception:
            logger.exception(f"Failed to convert response to object")
            return ResponseModel()
        verify_type(response_type.model, list)
        for i in response_type.model:
            model = obj_to_model(obj, i)
            if model is not None:
                return ResponseModel(
                    status=True,
                    content=model
                )
        return ResponseModel()
    elif response_type.type == ResponseTypes.json:
        try:
            return ResponseModel(
                status=True,
                content=response.json()
            )
        except Exception:
            logger.exception(f"Failed to convert response to object")
            return ResponseModel()
    elif response_type.type == ResponseTypes.raw_response:
        return ResponseModel(
            status=True,
            content=response
        )
    elif response_type.type == ResponseTypes.json_to_list_of_models:
        try:
            obj = response.json()
        except Exception:
            logger.exception(f"Failed to convert response to object")
            return ResponseModel()
        verify_none(response_type.model)
        verify_type(obj, list)
        parsed_lists = []
        for i in obj:
            model = obj_to_model(i, response_type.model)
            if model is not None:
                parsed_lists.append(model)
            else:
                return ResponseModel()
        return ResponseModel(
            status=True,
            content=parsed_lists
        )
    elif response_type.type == ResponseTypes.xml_to_model:
        try:
            obj = xmltodict.parse(response.text, encoding="utf-8")
        except Exception:
            logger.exception(f"Failed to convert response to xml object")
            return ResponseModel()
        verify_none(response_type.model)
        verify_type(obj, dict)
        model = obj_to_model(obj, response_type.model)
        if model is not None:
            return ResponseModel(
                status=True,
                content=model
            )
        else:
            return ResponseModel()
    elif response_type.type == ResponseTypes.jsonp_to_model:
        try:
            obj = json.loads(parse_jsonp(response.text))
        except Exception:
            logger.exception(f"Failed to convert response to json")
            return ResponseModel()
        verify_none(response_type.model)
        model = obj_to_model(obj, response_type.model)
        if model is not None:
            return ResponseModel(
                status=True,
                content=model
            )
        else:
            return ResponseModel()
    else:
        verify_not_used("web_request => response_type", "declaration (exhaustive handling)")
