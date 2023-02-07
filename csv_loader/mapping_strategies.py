from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, cast

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
    def validate_csv_loader_configuration(cls, csv_loader: object) -> bool:
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
        # map model field names as dict keys
        return dict(zip(self.field_names, row_values))


class MappingStrategyByHeader(MappingStrategyBase):
    """Implements by-header assignment. Header must be present."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.header: List[str] = []

    @classmethod
    def validate_csv_loader_configuration(cls, csv_loader: object) -> bool:
        # avoid circular imports and keep mypy happy
        from .csv_loader import CSVLoader
        csv_loader = cast(CSVLoader, csv_loader)

        if not csv_loader.has_header:
            raise HeaderNotSetError()

        return True

    def create_model_param_dict(
        self, row_index: int, row_values: List[Any]
    ) -> Dict[str, Any]:
        # assume it's header in line 0
        if row_index == 0:
            self.header = row_values

        # header not set? stop! hammer time!
        if not self.header:
            raise HeaderNotSetError()

        # header too short, can't do
        if len(row_values) > len(self.header):
            raise IndexOutOfHeaderBounds()

        # map header values as dict keys
        return dict(zip(self.header, row_values))
