from ctypes import Union
from typing import Dict, Iterable, List, Any, Optional, Type
from pydantic import BaseModel
from pydantic import BaseModel, validator
from pydantic.fields import ModelField
from pydantic.typing import get_origin, get_args, is_union


# def is_optional_annotation(class_attr: Dict[str, Type]) -> bool:
#     return get_origin(class_attr) is Union and get_args(class_attr)[1] is type(None)


class CSVRow(BaseModel):
    class Config:
        anystr_strip_whitespace = True
        empty_optional_str_to_none = True

    @validator("*", pre=True)
    def prepare_value(cls, value: Any, field: ModelField) -> Optional[Any]:
        # special handling for strings
        if isinstance(value, str):
            # strip whitespace if provided value is string
            if cls.Config.anystr_strip_whitespace:
                value = value.strip()
            # if string field is optional with 0 length, set it to None
            if len(value) == 0 and cls.Config.empty_optional_str_to_none:
                origin = get_origin(field.annotation)
                args = get_args(field.annotation)
                if is_union(origin) and args[1] is type(None):
                    return None

        # empty value and field type is not string? return None
        if value == "" and field.type_ is not str:
            return None

        # all good
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
