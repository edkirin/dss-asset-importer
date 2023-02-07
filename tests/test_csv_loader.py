import csv
from typing import Optional
from unittest import TestCase

import pytest
from pydantic import BaseModel, ValidationError

from csv_loader import (
    CSVLoader,
    CSVLoaderResult,
    CSVRow,
    CSVRows,
    MappingStrategyByHeader,
    MappingStrategyByModelFieldOrder,
)
from csv_loader.errors import (
    CSVValidationError,
    HeaderNotSetError,
    IndexOutOfHeaderBounds,
)


class DefaultCSVRow(CSVRow):
    field_int: int
    field_str: str
    field_float: float
    field_opt_int: Optional[int]
    field_opt_str: Optional[str]
    field_opt_float: Optional[float]

    class Config:
        anystr_strip_whitespace = True
        empty_optional_str_fields_to_none = ("__all__",)


class TestCSVRowValidation(TestCase):
    def test_happy_case(self):
        row = DefaultCSVRow(
            **{
                "field_int": 123,
                "field_str": "first string",
                "field_float": 234.567,
                "field_opt_int": 456,
                "field_opt_str": "second string",
                "field_opt_float": 345.678,
            }
        )
        assert row.field_int == 123
        assert row.field_str == "first string"
        assert row.field_float == 234.567
        assert row.field_opt_int == 456
        assert row.field_opt_str == "second string"
        assert row.field_opt_float == 345.678

    def test_trim_strings(self):
        row = DefaultCSVRow(
            **{
                "field_int": "     \n\n\n 123\t\t\n   \n\t",
                "field_str": "   first string   ",
                "field_float": "    \n\n\t \t\t \n234.567\t\t    \n",
                "field_opt_int": "    456      \n\n \t \n \t \t",
                "field_opt_str": "\n\n   second string\t\t   \n    \n",
                "field_opt_float": None,
            }
        )
        assert row.field_int == 123
        assert row.field_str == "first string"
        assert row.field_float == 234.567
        assert row.field_opt_int == 456
        assert row.field_opt_str == "second string"
        assert row.field_opt_float is None

    def test_convert_optional_empty_strings_to_none(self):
        row = DefaultCSVRow(
            **{
                "field_int": 123,
                "field_str": "",
                "field_float": 234.567,
                "field_opt_str": "",
            }
        )
        assert row.field_str == ""
        assert row.field_opt_str is None

    def test_empty_nonstring_convert_to_none(self):
        row = DefaultCSVRow(
            **{
                "field_int": 123,
                "field_str": "",
                "field_float": 234.567,
                "field_opt_int": "",
                "field_opt_str": "",
                "field_opt_float": "",
            }
        )
        assert row.field_int == 123
        assert row.field_str == ""
        assert row.field_float == 234.567
        assert row.field_opt_int is None
        assert row.field_opt_str is None
        assert row.field_opt_float is None

    def test_convert_configured_optional_empty_strings_to_none(self):
        class ModelRow(CSVRow):
            field_opt_str_1: Optional[str]
            field_opt_str_2: Optional[str]
            field_opt_str_3: Optional[str]
            field_opt_str_4: Optional[str]
            field_opt_str_5: Optional[str]
            field_str_dont_touch_6: str
            field_str_dont_touch_7: str
            field_str_dont_touch_8: str

            class Config:
                anystr_strip_whitespace = True
                empty_optional_str_fields_to_none = (
                    "field_opt_str_1",
                    "field_opt_str_3",
                    "field_opt_str_5",
                    "field_str_dont_touch_6",
                    "field_str_dont_touch_7",
                    "field_str_dont_touch_8",
                )

        row = ModelRow(
            **{
                "field_opt_str_1": "",
                "field_opt_str_2": "",
                "field_opt_str_3": "",
                "field_opt_str_4": "",
                "field_opt_str_5": "",
                "field_str_dont_touch_6": "",
                "field_str_dont_touch_7": "",
                "field_str_dont_touch_8": "",
            }
        )
        assert row.field_opt_str_1 is None
        assert row.field_opt_str_2 == ""
        assert row.field_opt_str_3 is None
        assert row.field_opt_str_4 == ""
        assert row.field_opt_str_5 is None
        assert row.field_str_dont_touch_6 == ""
        assert row.field_str_dont_touch_7 == ""
        assert row.field_str_dont_touch_8 == ""


class TestCSVRows(TestCase):
    class Model(CSVRow):
        id: int
        value: str

    def setup_method(self, method):
        self.model_list = CSVRows[TestCSVRows.Model](
            [
                TestCSVRows.Model(id=1, value="abc"),
                TestCSVRows.Model(id=2, value="def"),
                TestCSVRows.Model(id=3, value="ghi"),
                TestCSVRows.Model(id=4, value="jkl"),
                TestCSVRows.Model(id=5, value="mno"),
                TestCSVRows.Model(id=6, value="mno"),
                TestCSVRows.Model(id=7, value="mno"),
                TestCSVRows.Model(id=8, value="mno"),
                TestCSVRows.Model(id=9, value="xyz"),
            ]
        )

    def test_get_field_values(self):
        assert self.model_list.get_field_values("id") == [1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert set(self.model_list.get_field_values("value")) == {
            "abc",
            "def",
            "ghi",
            "jkl",
            "mno",
            "mno",
            "mno",
            "mno",
            "xyz",
        }

    def test_get_field_values_unique(self):
        assert self.model_list.get_field_values_unique("id") == [
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
        ]
        assert set(self.model_list.get_field_values_unique("value")) == {
            "abc",
            "def",
            "ghi",
            "jkl",
            "mno",
            "xyz",
        }


class TestCSVLoaderResult(TestCase):
    def test_initial_values(self):
        result = CSVLoaderResult[DefaultCSVRow]()
        assert len(result.rows) == 0
        assert len(result.errors) == 0
        assert len(result.header) == 0
        assert result.has_errors() is False


class SimpleFixtureFileRow(CSVRow):
    index: int
    organization_id: Optional[str]
    random_letters: str


class RandomPersonsFixtureFileRow(CSVRow):
    index: int
    mandatory_str: str
    optional_str: Optional[str]
    mandatory_int: int
    optional_int: Optional[int]
    mandatory_float: float
    optional_float: Optional[float]


class RandomPersonsFixtureFileRowWithHeaderMapping(CSVRow):
    mandatory_str: str
    mandatory_float: float
    index: int
    mandatory_int: int
    optional_float: Optional[float]
    optional_str: Optional[str]
    optional_int: Optional[int]


class RandomPersonsFixtureFileEmptyStrRow(RandomPersonsFixtureFileRow):
    class Config:
        anystr_strip_whitespace = True
        empty_optional_str_fields_to_none = ("",)


class ErrorFixtureFileRow(CSVRow):
    a: int
    b: int
    c: int
    d: int


class TestCSVLoader(TestCase):
    def test_read_csv_file_1(self):
        with open("fixtures/simple.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            csv_loader = CSVLoader[SimpleFixtureFileRow](
                reader=reader,
                output_model_cls=SimpleFixtureFileRow,
                has_header=True,
                aggregate_errors=True,
            )
            result = csv_loader.read_rows()

        assert result.rows == [
            SimpleFixtureFileRow(
                index=1, organization_id="FAB0d41d5b5d22c", random_letters="AAA"
            ),
            SimpleFixtureFileRow(index=2, organization_id=None, random_letters="BBB"),
            SimpleFixtureFileRow(
                index=3, organization_id="0bFED1ADAE4bcC1", random_letters="CCC"
            ),
            SimpleFixtureFileRow(
                index=4, organization_id="2bFC1Be8a4ce42f", random_letters=""
            ),
        ]
        assert result.has_errors() is False
        assert result.header == ["Index", "Organization Id", "Random letters"]

    def test_read_csv_random_persons__with_optional_none_strings(self):
        with open("fixtures/random-person.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            csv_loader = CSVLoader[RandomPersonsFixtureFileRow](
                reader=reader,
                output_model_cls=RandomPersonsFixtureFileRow,
                has_header=True,
                aggregate_errors=True,
            )
            result = csv_loader.read_rows()

        expected = [
            RandomPersonsFixtureFileRow(
                index=1,
                mandatory_str="Tyler",
                optional_str="Martin",
                mandatory_int=0,
                optional_int=0,
                mandatory_float=-2509.91694,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRow(
                index=2,
                mandatory_str="Hunter",
                optional_str=None,
                mandatory_int=20,
                optional_int=1,
                mandatory_float=-15221.35845,
                optional_float=-95947.2111,
            ),
            RandomPersonsFixtureFileRow(
                index=3,
                mandatory_str="Kevin",
                optional_str="Sanchez",
                mandatory_int=8,
                optional_int=None,
                mandatory_float=40050.61689,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRow(
                index=4,
                mandatory_str="Christopher",
                optional_str="Freeman",
                mandatory_int=9,
                optional_int=7,
                mandatory_float=74859.09668,
                optional_float=-46270.42507,
            ),
            RandomPersonsFixtureFileRow(
                index=5,
                mandatory_str="Bryan",
                optional_str="Hall",
                mandatory_int=5,
                optional_int=None,
                mandatory_float=-17964.3768,
                optional_float=-67664.05305,
            ),
            RandomPersonsFixtureFileRow(
                index=6,
                mandatory_str="Ricky",
                optional_str=None,
                mandatory_int=81,
                optional_int=7,
                mandatory_float=59494.01444,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRow(
                index=7,
                mandatory_str="Anna",
                optional_str=None,
                mandatory_int=7,
                optional_int=6,
                mandatory_float=98680.42175,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRow(
                index=8,
                mandatory_str="Angelica",
                optional_str="Evans",
                mandatory_int=27,
                optional_int=None,
                mandatory_float=58478.98207,
                optional_float=58604.80922,
            ),
            RandomPersonsFixtureFileRow(
                index=9,
                mandatory_str="Patricia",
                optional_str="Brewer",
                mandatory_int=2,
                optional_int=None,
                mandatory_float=-8726.879,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRow(
                index=10,
                mandatory_str="John",
                optional_str="Mitchell",
                mandatory_int=60,
                optional_int=None,
                mandatory_float=93534.83911,
                optional_float=None,
            ),
        ]
        assert result.rows == expected
        assert result.has_errors() is False
        assert result.header == [
            "index",
            "mandatory str",
            "optional str",
            "mandatory int",
            "optional int",
            "mandatory float",
            "optional float",
        ]

    def test_read_csv_random_persons__with_optional_none_strings__and_header_mapping_strategy(
        self,
    ):
        with open("fixtures/random-person-with-header-mapping.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            csv_loader = CSVLoader[RandomPersonsFixtureFileRowWithHeaderMapping](
                reader=reader,
                output_model_cls=RandomPersonsFixtureFileRowWithHeaderMapping,
                has_header=True,
                aggregate_errors=True,
                mapping_strategy=MappingStrategyByHeader(
                    model_cls=RandomPersonsFixtureFileRowWithHeaderMapping
                ),
            )
            result = csv_loader.read_rows()

        expected = [
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=1,
                mandatory_str="Tyler",
                optional_str="Martin",
                mandatory_int=0,
                optional_int=0,
                mandatory_float=-2509.91694,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=2,
                mandatory_str="Hunter",
                optional_str=None,
                mandatory_int=20,
                optional_int=1,
                mandatory_float=-15221.35845,
                optional_float=-95947.2111,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=3,
                mandatory_str="Kevin",
                optional_str="Sanchez",
                mandatory_int=8,
                optional_int=None,
                mandatory_float=40050.61689,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=4,
                mandatory_str="Christopher",
                optional_str="Freeman",
                mandatory_int=9,
                optional_int=7,
                mandatory_float=74859.09668,
                optional_float=-46270.42507,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=5,
                mandatory_str="Bryan",
                optional_str="Hall",
                mandatory_int=5,
                optional_int=None,
                mandatory_float=-17964.3768,
                optional_float=-67664.05305,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=6,
                mandatory_str="Ricky",
                optional_str=None,
                mandatory_int=81,
                optional_int=7,
                mandatory_float=59494.01444,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=7,
                mandatory_str="Anna",
                optional_str=None,
                mandatory_int=7,
                optional_int=6,
                mandatory_float=98680.42175,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=8,
                mandatory_str="Angelica",
                optional_str="Evans",
                mandatory_int=27,
                optional_int=None,
                mandatory_float=58478.98207,
                optional_float=58604.80922,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=9,
                mandatory_str="Patricia",
                optional_str="Brewer",
                mandatory_int=2,
                optional_int=None,
                mandatory_float=-8726.879,
                optional_float=None,
            ),
            RandomPersonsFixtureFileRowWithHeaderMapping(
                index=10,
                mandatory_str="John",
                optional_str="Mitchell",
                mandatory_int=60,
                optional_int=None,
                mandatory_float=93534.83911,
                optional_float=None,
            ),
        ]
        assert result.rows == expected
        assert result.has_errors() is False
        assert result.header == [
            "index",
            "mandatory_str",
            "optional_str",
            "mandatory_int",
            "optional_int",
            "mandatory_float",
            "optional_float",
        ]

    def test_read_csv_random_persons__with_optional_empty_strings(self):
        with open("fixtures/random-person.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            csv_loader = CSVLoader[RandomPersonsFixtureFileEmptyStrRow](
                reader=reader,
                output_model_cls=RandomPersonsFixtureFileEmptyStrRow,
                has_header=True,
                aggregate_errors=True,
            )
            result = csv_loader.read_rows()

        expected = [
            RandomPersonsFixtureFileEmptyStrRow(
                index=1,
                mandatory_str="Tyler",
                optional_str="Martin",
                mandatory_int=0,
                optional_int=0,
                mandatory_float=-2509.91694,
                optional_float=None,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=2,
                mandatory_str="Hunter",
                optional_str="",
                mandatory_int=20,
                optional_int=1,
                mandatory_float=-15221.35845,
                optional_float=-95947.2111,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=3,
                mandatory_str="Kevin",
                optional_str="Sanchez",
                mandatory_int=8,
                optional_int=None,
                mandatory_float=40050.61689,
                optional_float=None,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=4,
                mandatory_str="Christopher",
                optional_str="Freeman",
                mandatory_int=9,
                optional_int=7,
                mandatory_float=74859.09668,
                optional_float=-46270.42507,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=5,
                mandatory_str="Bryan",
                optional_str="Hall",
                mandatory_int=5,
                optional_int=None,
                mandatory_float=-17964.3768,
                optional_float=-67664.05305,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=6,
                mandatory_str="Ricky",
                optional_str="",
                mandatory_int=81,
                optional_int=7,
                mandatory_float=59494.01444,
                optional_float=None,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=7,
                mandatory_str="Anna",
                optional_str="",
                mandatory_int=7,
                optional_int=6,
                mandatory_float=98680.42175,
                optional_float=None,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=8,
                mandatory_str="Angelica",
                optional_str="Evans",
                mandatory_int=27,
                optional_int=None,
                mandatory_float=58478.98207,
                optional_float=58604.80922,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=9,
                mandatory_str="Patricia",
                optional_str="Brewer",
                mandatory_int=2,
                optional_int=None,
                mandatory_float=-8726.879,
                optional_float=None,
            ),
            RandomPersonsFixtureFileEmptyStrRow(
                index=10,
                mandatory_str="John",
                optional_str="Mitchell",
                mandatory_int=60,
                optional_int=None,
                mandatory_float=93534.83911,
                optional_float=None,
            ),
        ]
        assert result.rows == expected
        assert result.has_errors() is False
        assert result.header == [
            "index",
            "mandatory str",
            "optional str",
            "mandatory int",
            "optional int",
            "mandatory float",
            "optional float",
        ]

    def test_stop_on_first_error(self):
        with open("fixtures/errors.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            csv_loader = CSVLoader[ErrorFixtureFileRow](
                reader=reader,
                output_model_cls=ErrorFixtureFileRow,
                has_header=False,
                aggregate_errors=False,
            )

            with pytest.raises(CSVValidationError) as ex:
                csv_loader.read_rows()

            assert isinstance(ex.value, CSVValidationError)
            assert ex.value.line_number == 0
            assert (
                isinstance(ex.value.original_error, ValidationError)
                and len(ex.value.original_error.raw_errors) == 4
            )

    def test_aggregate_errors(self):
        with open("fixtures/errors.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            csv_loader = CSVLoader[ErrorFixtureFileRow](
                reader=reader,
                output_model_cls=ErrorFixtureFileRow,
                has_header=False,
                aggregate_errors=True,
            )
            result = csv_loader.read_rows()

            assert result.has_errors()
            assert len(result.errors) == 2
            assert isinstance(result.errors[0], CSVValidationError)
            assert isinstance(result.errors[1], CSVValidationError)
            assert result.errors[0].line_number == 0
            assert result.errors[1].line_number == 1

    def test_use_mapping_strategy_by_header__fail_without_has_headers_option(self):
        with open("fixtures/errors.csv") as csv_file:
            reader = csv.reader(csv_file, delimiter=",")

            with pytest.raises(HeaderNotSetError):
                CSVLoader[ErrorFixtureFileRow](
                    reader=reader,
                    output_model_cls=ErrorFixtureFileRow,
                    has_header=False,
                    aggregate_errors=True,
                    mapping_strategy=MappingStrategyByHeader(
                        model_cls=ErrorFixtureFileRow
                    ),
                )


class DummyModel(BaseModel):
    field_1: str
    field_2: str
    field_3: str


class TestMappingStrategyByModelFieldOrder(TestCase):
    def test_create_model_param_dict(self):
        mapping = MappingStrategyByModelFieldOrder(model_cls=DummyModel)
        row_values = [111, 222, 333]
        result = mapping.create_model_param_dict(row_values=row_values)

        assert result == {
            "field_1": 111,
            "field_2": 222,
            "field_3": 333,
        }


class TestMappingStrategyByHeader(TestCase):
    def test_create_model_param_dict(self):
        header = ["header_field_1", "header_field_2", "header_field_3"]
        row_values = [111, 222, 333]

        mapping = MappingStrategyByHeader(model_cls=DummyModel)
        mapping.set_header(header)

        result = mapping.create_model_param_dict(row_values=row_values)
        assert result == {
            "header_field_1": 111,
            "header_field_2": 222,
            "header_field_3": 333,
        }

    def test_create_model_param_dict__fail_without_header(self):
        row_values = [111, 222, 333]
        mapping = MappingStrategyByHeader(model_cls=DummyModel)

        with pytest.raises(HeaderNotSetError):
            mapping.create_model_param_dict(row_values=row_values)

    def test_create_model_param_dict__fail_index_out_of_header_bounds(self):
        header = ["header_field_1", "header_field_2", "header_field_3"]
        row_values = [111, 222, 333, 444]

        mapping = MappingStrategyByHeader(model_cls=DummyModel)
        mapping.set_header(header)

        with pytest.raises(IndexOutOfHeaderBounds):
            mapping.create_model_param_dict(row_values=row_values)
