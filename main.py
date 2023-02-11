import csv
import time
from typing import Optional

from csv_loader import CSVLoader, CSVRow
from csv_loader.csv_loader import BoolValuePair, CSVRowDefaultConfig


class Example1Row(CSVRow):
    index: int
    organization_id: str
    name: str
    random_float: Optional[float]
    website: str
    country: str
    description: str
    founded: int
    industry: str
    number_of_employees: int


class Example2Row(CSVRow):
    index: int
    organization_id: Optional[str]
    random_letters: str


class BigDatasetRow(CSVRow):
    index: int
    first_name: str
    last_name: str
    street_address: str
    city: str
    country: str
    iban: str
    barcode_1: str
    barcode_2: str
    barcode_3: str
    float_1: float
    float_2: float
    float_3: float
    float_4: float
    float_5: float
    int_1: int
    int_2: int
    int_3: int
    int_4: int
    int_5: int
    bool_1: bool
    bool_2: bool
    bool_3: bool
    bool_4: bool
    bool_5: bool

    class Config(CSVRowDefaultConfig):
        bool_value_pair = BoolValuePair(true="YES", false="NO")


def process_example_1() -> None:
    print("Processing Example 1")

    with open("csv_examples/example-1.csv") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")

        csv_loader = CSVLoader[Example1Row](
            reader=reader,
            output_model_cls=Example1Row,
            has_header=True,
            aggregate_errors=True,
        )

        result = csv_loader.read_rows()
        if result.has_errors():
            for error in result.errors:
                print(error)
        else:
            for row in result.rows:
                print(row.index, row.organization_id)
            print(result.header)

        print("-" * 50)
        duplicates = result.rows.get_field_duplicates(field_name="organization_id")
        print(duplicates)


def process_example_2() -> None:
    print("Processing Example 2")

    with open("csv_examples/example-2.csv") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")

        csv_loader = CSVLoader[Example2Row](
            reader=reader,
            output_model_cls=Example2Row,
            has_header=True,
        )

        result = csv_loader.read_rows()
        for row in result.rows:
            print(row)


def process_big_data() -> None:
    print("Processing Big Data")
    t = time.perf_counter()

    with open("/tmp/big-data-set-100.000.csv") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")

        csv_loader = CSVLoader[BigDatasetRow](
            reader=reader,
            output_model_cls=BigDatasetRow,
            has_header=True,
            aggregate_errors=True,
        )

        result = csv_loader.read_rows()
        # print(f"Row count: {len(result.rows)}")
        if result.has_errors():
            for error in result.errors:
                print(error)
        # else:
        #     for row in result.rows:
        #         print(
        #             row.index,
        #             row.bool_1,
        #             row.bool_2,
        #             row.bool_3,
        #             row.bool_4,
        #             row.bool_5,
        #         )

    t_elapsed = time.perf_counter() - t
    print(f"[T] load and parse CSV file: {t_elapsed:0.3f}")

    t = time.perf_counter()
    field_name = "int_1"
    duplicates = result.rows.get_field_duplicates(field_name=field_name)
    # print(duplicates)

    t_elapsed = time.perf_counter() - t
    print(f"[T] find duplicates ({field_name}): {t_elapsed:0.3f}")
    print(f"duplicates found: {len(duplicates)}")
    t = time.perf_counter()


def main() -> None:
    # process_example_1()
    # process_example_2()
    process_big_data()


if __name__ == "__main__":
    main()
