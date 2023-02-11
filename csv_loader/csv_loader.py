from __future__ import annotations

import collections
from dataclasses import dataclass
from typing import Any, Dict, Generic, Iterable, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError, validator
from pydantic.fields import ModelField

from .errors import CSVValidationError, MappingStrategyError
from .mapping_strategies import MappingStrategyByModelFieldOrder

CSVReaderType = Iterable[List[str]]


@dataclass
class BoolValuePair:
    true: str
    false: str


@dataclass
class CSVFieldDuplicate:
    value: Any
    duplicate_rows: List[int]


class CSVRowDefaultConfig:
    anystr_strip_whitespace: bool = True
    """Standard pydantic config flag, set default to True."""
    empty_optional_str_fields_to_none: Tuple = ("__all__",)
    """List of optional string fields which will be converted to None, if empty.
    Default magic value is "__all__" to convert all fields."""
    bool_value_pair = BoolValuePair(true="1", false="0")
    """Possible boolean values for true and false. If the actual value
    is not in defined pair, value will be parsed as None."""


class CSVRow(BaseModel):
    """
    Represents a model base for a single CSV row and implements special handling for string values.
    If given field value is empty, but annotated type is not string, it will be converted to None.
    This is useful for basic types (int, float), to be converted to None if value is not provided.
    It's assumed those fields are annotated as Optional, otherwise pydantic will raise expected
    validation error.
    See Config inner class for more options.
    """

    class Config(CSVRowDefaultConfig):
        """
        Defaults from CSVRowDefaultConfig will be used. If you're defining your own Config in
        custom CSVRow class, make sure it inherits `CSVRowDefaultConfig`
        """

    @validator("*", pre=True)
    def prepare_str_value(
        cls: CSVRow, value: Any, field: ModelField  # noqa: ANN401
    ) -> Optional[Any]:
        # not a string? just return value, pydantic validator will do the rest
        if not isinstance(value, str):
            return value
        # strip whitespace if config say so
        if cls.Config.anystr_strip_whitespace:
            value = value.strip()

        # special handling for bool values
        if field.type_ is bool:
            if value == cls.Config.bool_value_pair.true:
                return True
            if value == cls.Config.bool_value_pair.false:
                return False
            return None

        # no special handling for non-empty strings
        if len(value) > 0:
            return value
        # empty value and annotated field type is not string? return None
        if field.type_ is not str:
            return None
        # if string field is annotated as optional with 0 length, set it to None
        if (
            "__all__" in cls.Config.empty_optional_str_fields_to_none
            or field.name in cls.Config.empty_optional_str_fields_to_none
        ) and not field.required:
            return None
        return value


CSVLoaderModelType = TypeVar("CSVLoaderModelType", bound=BaseModel)


class CSVRows(List[CSVLoaderModelType]):
    """Generic parsed CSV rows containing pydantic models."""

    def get_field_values(self, field_name: str) -> List[Any]:
        """Get list of all values from models for named field.
        Field value order is preserved."""
        return [getattr(row, field_name) for row in self]

    def get_field_values_unique(self, field_name: str) -> List[Any]:
        """Get list of all unique values from models for named field, without duplicates.
        Field value order is not preserved."""
        return list(set(self.get_field_values(field_name)))

    def field_has_duplicates(self, field_name: str, value: Any) -> bool:
        return value in self.get_field_values(field_name)

    def get_field_duplicates(self, field_name: str) -> List[CSVFieldDuplicate]:
        check_dict: Dict[Any, List] = {}
        all_field_values = self.get_field_values(field_name)

        for row_index, value in enumerate(all_field_values):
            if value in check_dict:
                check_dict[value].append(row_index)
            else:
                check_dict[value] = [row_index]

        result: List[CSVFieldDuplicate] = [
            CSVFieldDuplicate(
                value=value,
                duplicate_rows=found_in_rows,
            )
            for value, found_in_rows in check_dict.items()
            if len(found_in_rows) > 1
        ]

        return result


class CSVLoaderResult(Generic[CSVLoaderModelType]):
    """Generic CSVLoader result. Contains parsed pydantic models, aggregated errors and header content."""

    def __init__(self) -> None:
        self.rows: CSVRows[CSVLoaderModelType] = CSVRows()
        self.errors: List[CSVValidationError] = []
        self.header: List[str] = []

    def has_errors(self) -> bool:
        return len(self.errors) > 0


class CSVLoader(Generic[CSVLoaderModelType]):
    """
    Generic CSV file parser.
    Uses standard csv reader to fetch csv rows, validate against provided
    pydantic model and returns list of created models together with
    aggregated error list.

    Example:

        with open("data.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            csv_loader = CSVLoader[MyRowModel](
                reader=reader,
                output_model_cls=MyRowModel,
                has_header=True,
                aggregate_errors=True,
            )

            result = csv_loader.read_rows()
            if result.has_errors():
                print("Errors:")
                for error in result.errors:
                    print(error)

            print("Created models:")
            for row in result.rows:
                print(row.index, row.organization_id)

        See tests/adapters/tools/test_csv_loader.py for more examples.
    """

    def __init__(
        self,
        reader: CSVReaderType,
        output_model_cls: Type[CSVLoaderModelType],
        has_header: Optional[bool] = True,
        aggregate_errors: Optional[bool] = False,
        mapping_strategy: Optional[MappingStrategyByModelFieldOrder] = None,
    ) -> None:
        self.reader = reader
        self.output_model_cls = output_model_cls
        self.has_header = has_header
        self.aggregate_errors = aggregate_errors

        if mapping_strategy:
            self.mapping_strategy = mapping_strategy
        else:
            self.mapping_strategy = MappingStrategyByModelFieldOrder(
                model_cls=self.output_model_cls,
            )

        self.mapping_strategy.validate_csv_loader_configuration(csv_loader=self)

    def read_rows(self) -> CSVLoaderResult[CSVLoaderModelType]:
        result = CSVLoaderResult[CSVLoaderModelType]()

        for line_number, row in enumerate(self.reader):
            # skip header, if configured and first line
            if self.has_header and line_number == 0:
                # strip header field names
                header = [field.strip() for field in row]
                result.header = header
                self.mapping_strategy.set_header(header)
                continue

            # skip empty lines
            if not row:
                continue

            row_model = None
            try:
                # create model kwargs params using mapping strategy
                model_create_kwargs = self.mapping_strategy.create_model_param_dict(
                    row_values=row,
                )
                # create output model from row data
                row_model = self.output_model_cls(**model_create_kwargs)
            except (MappingStrategyError, ValidationError) as ex:
                # create extended error object
                error = CSVValidationError(
                    line_number=line_number,
                    original_error=ex,
                )
                if self.aggregate_errors:
                    # if we're aggregating errors, just add exception to the list
                    result.errors.append(error)
                else:
                    # else just raise error and stop reading rows
                    raise error

            # row_model will be None if creation fails and error aggregation is active
            if row_model is not None:
                result.rows.append(row_model)

        return result
