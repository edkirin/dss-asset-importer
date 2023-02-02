from typing import Any, Iterable, List, Optional, Type, Union

from pydantic import BaseModel, validator
from pydantic.fields import ModelField
from pydantic.typing import get_args, get_origin


class CSVRow(BaseModel):
    """
    Represents a model base for a single CSV row and implements special handling for string values.
    If given field value is empty, but annotated type is not string, it will be converted to None.
    This is useful for basic types (int, float), to be converted to None if value is not provided.
    It's assumed those fields are annotated as Optional, otherwise pydantic will raise expected
    validation error.
    If given field type is optional string and provided value is empty, Config.empty_optional_str_to_none
    will force it to None.
    """

    class Config:
        anystr_strip_whitespace = True
        empty_optional_str_to_none = True

    @validator("*", pre=True)
    def prepare_str_value(cls, value: Any, field: ModelField) -> Optional[Any]:
        # not a string? just return value, pydantic validator will do the rest
        if not isinstance(value, str):
            return value
        # strip whitespace if config say so
        if cls.Config.anystr_strip_whitespace:
            value = value.strip()
        # no special handling for non-empty strings
        if len(value) > 0:
            return value
        # empty value and field type is not string? return None
        if field.type_ is not str:
            return None
        # if string field is optional with 0 length, set it to None
        if (
            cls.Config.empty_optional_str_to_none
            and get_origin(field.annotation) is Union
            and get_args(field.annotation)[1] is type(None)
        ):
            return None
        return value


class CSVLoader:
    def __init__(
        self,
        reader: Iterable[List[str]],
        output_model_cls: Type[BaseModel],
        has_header: Optional[bool] = True,
    ):
        self.reader = reader
        self.has_header = has_header
        self.output_model_cls = output_model_cls

    def read_to_models(self) -> List[BaseModel]:
        row_models: List[BaseModel] = []

        field_names = self.output_model_cls.__fields__.keys()

        for index, row in enumerate(self.reader):
            if self.has_header and index == 0:
                continue

            kwargs = dict(zip(field_names, row))
            model = self.output_model_cls(**kwargs)
            row_models.append(model)

        return row_models
