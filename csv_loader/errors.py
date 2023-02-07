class CSVValidationError(Exception):
    """Extended validation exception class containing additional attributes."""

    def __init__(self, line_number: int, original_error: Exception) -> None:
        self.line_number = line_number
        self.original_error = original_error

    def __str__(self) -> str:
        return f"Error at line {self.line_number}: {self.original_error}"


class MappingStrategyError(Exception):
    ...


class HeaderNotSetError(MappingStrategyError):
    detail = "Header must be set in order to use MappingStrategyByHeader"


class IndexOutOfHeaderBounds(MappingStrategyError):
    detail = "Row value index out of header bounds"
