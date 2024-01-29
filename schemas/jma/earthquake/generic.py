from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas.eew import SvirLgIntensityEnum
from schemas.jma.tsunami_expectation import JMAWarningCommentModel


class JMAEqCommentModel(BaseModel):
    forecast_comment: Optional[JMAWarningCommentModel] = Field(None, validation_alias="ForecastComment")
    var_comment: Optional[JMAWarningCommentModel] = Field(None, validation_alias="VarComment")
    freeform_comment: Optional[str] = Field(None, validation_alias="FreeFormComment")


class JMAIntensityEnum(Enum):
    no = "不明"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five_lower = "5-"
    five_upper = "5+"
    bigger_than_five_lower = "震度５弱以上未入電"
    six_lower = "6-"
    six_upper = "6+"
    seven = "7"

    @classmethod
    def _missing_(cls, value: object):
        return cls.no


JMALgIntensityEnum = SvirLgIntensityEnum
