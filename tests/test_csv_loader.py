from typing import Optional
from unittest import TestCase
from csv_loader import CSVRow


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


class TestCSVRow(TestCase):
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
