from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type

from pydantic import BaseModel

from csv_loader.errors import HeaderNotSetError, IndexOutOfHeaderBounds


class MappingStrategyBase(ABC):
    """
    Mapping strategy implements mechanism of creating params (kwargs) dict from
    row values which is later used in model creation.
    """

    def __init__(self, model_cls: Type[BaseModel]) -> None:
        self.model_cls = model_cls

    @abstractmethod
    def create_model_param_dict(
        self, row_index: int, row_values: List[Any]
    ) -> Dict[str, Any]:
        """Create initial model params dict."""

    @classmethod
    def verify_csv_loader_configuration(cls, csv_loader) -> bool:
        return True


class MappingStrategyByModelFieldOrder(MappingStrategyBase):
    """
    Implements 1:1 field assignment. Each row value is assigned to model attribute
    in order in which is defined in model.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.field_names = self.model_cls.__fields__.keys()

    def create_model_param_dict(
        self, row_index: int, row_values: List[Any]
    ) -> Dict[str, Any]:
        return dict(zip(self.field_names, row_values))


class MappingStrategyByHeader(MappingStrategyBase):
    """Implements by-header assignment. Header must be present"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.header: List[str] = []

    @classmethod
    def verify_csv_loader_configuration(cls, csv_loader) -> bool:
        if not csv_loader.has_header:
            raise HeaderNotSetError()
        return True

    def create_model_param_dict(
        self, row_index: int, row_values: List[Any]
    ) -> Dict[str, Any]:
        if row_index == 0:
            self.header = row_values

        if not self.header:
            raise HeaderNotSetError()

        header_len = len(self.header)
        param_dict = {}

        for index, field_value in enumerate(row_values):
            if index >= header_len:
                raise IndexOutOfHeaderBounds()

            field_name = self.header[index]
            param_dict[field_name] = field_value

        return param_dict