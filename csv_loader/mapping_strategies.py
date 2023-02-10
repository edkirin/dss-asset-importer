from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, cast

from pydantic import BaseModel

from .errors import HeaderNotSetError, IndexOutOfHeaderBounds


class MappingStrategyBase(ABC):
    """
    Mapping strategy implements mechanism of creating params (kwargs) dict from
    row values which is later used in model creation.
    """

    def __init__(self, model_cls: Type[BaseModel]) -> None:
        self.model_cls = model_cls
        self.header: Optional[List[str]] = None

    def set_header(self, header: List[str]) -> None:
        self.header = header

    @abstractmethod
    def create_model_param_dict(self, row_values: List[Any]) -> Dict[str, Any]:
        """Create initial model params dict."""

    @classmethod
    def validate_csv_loader_configuration(cls: MappingStrategyBase, csv_loader: object) -> bool:
        return True


class MappingStrategyByModelFieldOrder(MappingStrategyBase):
    """
    Implements 1:1 field assignment. Each row value is assigned to model attribute
    in order in which is defined in model.
    """

    def __init__(self, model_cls: Type[BaseModel]) -> None:
        super().__init__(model_cls)
        self.field_names = self.model_cls.__fields__.keys()

    def create_model_param_dict(self, row_values: List[Any]) -> Dict[str, Any]:
        # map model field names as dict keys
        return dict(zip(self.field_names, row_values))


@dataclass
class HeaderRemapField:
    header_field: str
    model_attr: str


class MappingStrategyByHeader(MappingStrategyBase):
    """Implements by-header assignment. Header must be present."""

    def __init__(
        self,
        model_cls: Type[BaseModel],
        header_remap_fields: Optional[List[HeaderRemapField]] = None,
    ) -> None:
        super().__init__(model_cls)
        self.header: List[str] = []
        self.header_remap = header_remap_fields

    @classmethod
    def validate_csv_loader_configuration(
        cls: MappingStrategyByHeader, csv_loader: object
    ) -> bool:
        # avoid circular imports and keep mypy happy
        from .csv_loader import CSVLoader

        csv_loader = cast(CSVLoader, csv_loader)

        if not csv_loader.has_header:
            raise HeaderNotSetError()

        return True

    @staticmethod
    def _remap_header_mapping(
        header_mapping: Dict[str, Any], header_remap: Optional[List[HeaderRemapField]]
    ) -> Dict[str, Any]:
        if not header_remap:
            return header_mapping

        header_mapping = header_mapping.copy()

        for remap_field in header_remap:
            if remap_field.header_field in header_mapping:
                header_mapping[remap_field.model_attr] = header_mapping.pop(
                    remap_field.header_field
                )
        return header_mapping

    def create_model_param_dict(self, row_values: List[Any]) -> Dict[str, Any]:
        # header not set? stop! hammer time!
        if not self.header:
            raise HeaderNotSetError()

        # header too short, can't do
        if len(row_values) > len(self.header):
            raise IndexOutOfHeaderBounds()

        # map header values as dict keys
        header_mapping = dict(zip(self.header, row_values))

        header_mapping = self._remap_header_mapping(
            header_mapping=header_mapping, header_remap=self.header_remap
        )
        return header_mapping
