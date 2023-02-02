from typing import Iterable, List, Any, Optional, Type
from pydantic import BaseModel
from pydantic import BaseModel, validator
from pydantic.fields import ModelField


class CSVRow(BaseModel):
    class Config:
        anystr_strip_whitespace = True

    @validator("*", pre=True)
    def empty_str_to_none(cls, value: Any, field: ModelField):
        if isinstance(value, str) and cls.Config.anystr_strip_whitespace:
            value = value.strip()

        if value == "" and field.type_ is not str:
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
