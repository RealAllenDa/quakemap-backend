from enum import Enum
from typing import Any, Optional, TypeVar, Type

from pydantic import BaseModel

OnlyModel = TypeVar("OnlyModel", bound=Type[BaseModel])


class ResponseTypes(str, Enum):
    json_to_list_of_models = "json_to_list_of_models"
    json_to_model = "json_to_model"
    json_to_multiple_model = "json_to_multiple_model"
    json = "json"
    jsonp_to_model = "jsonp_to_model"
    raw_response = "raw_response"
    xml_to_model = "xml_to_model"


class ResponseTypeModel(BaseModel):
    type: ResponseTypes
    model: Optional[OnlyModel | list[OnlyModel]] = None


class ResponseModel(BaseModel):
    status: bool = False
    content: Any = None


class RequestTypes(str, Enum):
    post = "post"
    get = "get"
    delete = "delete"
