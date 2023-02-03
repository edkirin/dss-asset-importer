import csv
from typing import Optional
from unittest import TestCase

from csv_loader import CSVRow, CSVRows, CSVLoaderResult, CSVValidationError, CSVLoader


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
        assert set(self.model_list.get_field_values("value")) == set(
            [
                "abc",
                "def",
                "ghi",
                "jkl",
                "mno",
                "mno",
                "mno",
                "mno",
                "xyz",
            ]
        )

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
        assert set(self.model_list.get_field_values_unique("value")) == set(
            [
                "abc",
                "def",
                "ghi",
                "jkl",
                "mno",
                "xyz",
            ]
        )


class TestCSVLoaderResult(TestCase):
    def test_initial_values(self):
        result = CSVLoaderResult[DefaultCSVRow]()
        assert len(result.rows) == 0
        assert len(result.errors) == 0
        assert len(result.header) == 0
        assert result.has_errors() is False


CSV_FILE_1_CONTENT = """Index,  Organization Id ,Random letters
1,"FAB0d41d5b5d22c","  AAA "
2,,"BBB"
3,"0bFED1ADAE4bcC1","CCC"
4,"2bFC1Be8a4ce42f",""
"""


class CSVFile1Row(CSVRow):
    index: int
    organization_id: Optional[str]
    random_letters: str


class TestCSVLoader(TestCase):
    def test_read_csv_file_1(self):
        reader = csv.reader(CSV_FILE_1_CONTENT.splitlines(), delimiter=",")

        csv_loader = CSVLoader[CSVFile1Row](
            reader=reader,
            output_model_cls=CSVFile1Row,
            has_header=True,
            aggregate_errors=True,
        )
        result = csv_loader.read_rows()

        assert result.rows == [
            CSVFile1Row(
                index=1, organization_id="FAB0d41d5b5d22c", random_letters="AAA"
            ),
            CSVFile1Row(index=2, organization_id=None, random_letters="BBB"),
            CSVFile1Row(
                index=3, organization_id="0bFED1ADAE4bcC1", random_letters="CCC"
            ),
            CSVFile1Row(index=4, organization_id="2bFC1Be8a4ce42f", random_letters=""),
        ]
        assert result.has_errors() is False
        assert result.header == ["Index", "Organization Id", "Random letters"]
