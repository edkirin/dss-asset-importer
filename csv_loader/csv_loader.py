from typing import Any, Generic, Iterable, List, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError, validator
from pydantic.fields import ModelField
from pydantic.typing import get_args, get_origin

CSVReaderType = Iterable[List[str]]


class CSVValidationError(Exception):
    """Extended validation exception class containing additional attributes."""

    def __init__(self, line_number: int, original_error: ValidationError) -> None:
        self.line_number = line_number
        self.original_error = original_error

    def __str__(self) -> str:
        return f"Error at line {self.line_number}: {self.original_error}"


class CSVRow(BaseModel):
    """Represents a model base for a single CSV row and implements special handling for string values.
    If given field value is empty, but annotated type is not string, it will be converted to None.
    This is useful for basic types (int, float), to be converted to None if value is not provided.
    It's assumed those fields are annotated as Optional, otherwise pydantic will raise expected
    validation error.
    See Config inner class for more options.
    """

    class Config:
        anystr_strip_whitespace: bool = True
        """Standard pydantic config flag, set default to True."""
        empty_optional_str_fields_to_none: Tuple = ("__all__",)
        """List of optional string fields which will be converted to None, if empty.
        Default magic value is "__all__" to convert all fields."""

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
        # empty value and annotated field type is not string? return None
        if field.type_ is not str:
            return None
        # if string field is annotated as optional with 0 length, set it to None
        if (
            (
                "__all__" in cls.Config.empty_optional_str_fields_to_none
                or field.name in cls.Config.empty_optional_str_fields_to_none
            )
            and get_origin(field.annotation) is Union
            and get_args(field.annotation)[1] is type(None)
        ):
            return None
        return value


CSVLoaderModelType = TypeVar("CSVLoaderModelType", bound=BaseModel)


class CSVRows(List[CSVLoaderModelType]):
    """Generic parsed CSV rows containing pydantic models."""

    def get_field_values(self, field_name: str) -> List[Any]:
        """Get list of all values from models for named field."""
        return [getattr(row, field_name) for row in self]

    def get_field_values_unique(self, field_name: str) -> List[Any]:
        """Get list of all unique values from models for named field, without duplicates."""
        return list(set(self.get_field_values(field_name)))


class CSVLoaderResult(Generic[CSVLoaderModelType]):
    """Generic CSVLoader result. Contains parsed pydantic models, aggregated errors and header content."""

    def __init__(self) -> None:
        self.rows: CSVRows[CSVLoaderModelType] = CSVRows()
        self.errors: List[CSVValidationError] = []
        self.header: List[str] = []

    def has_errors(self) -> bool:
        return len(self.errors) > 0


class CSVLoader(Generic[CSVLoaderModelType]):
    """Generic CSV file parser."""

    def __init__(
        self,
        reader: CSVReaderType,
        output_model_cls: Type[CSVLoaderModelType],
        has_header: Optional[bool] = True,
        aggregate_errors: Optional[bool] = False,
    ) -> None:
        self.reader = reader
        self.output_model_cls = output_model_cls
        self.has_header = has_header
        self.aggregate_errors = aggregate_errors

    def read_rows(self) -> CSVLoaderResult[CSVLoaderModelType]:
        result = CSVLoaderResult[CSVLoaderModelType]()

        field_names = self.output_model_cls.__fields__.keys()

        for line_number, row in enumerate(self.reader):
            # skip empty lines
            if not row:
                continue

            # skip header, if configured
            if self.has_header and line_number == 0:
                result.header = [field.strip() for field in row]
                continue

            # create dict containing field_name: value
            kwargs = dict(zip(field_names, row))

            row_model = None
            try:
                # create output model from row data
                row_model = self.output_model_cls(**kwargs)
            except ValidationError as ex:
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

            if row_model is not None:
                result.rows.append(row_model)

        return result
