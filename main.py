import csv
from typing import Optional

from csv_loader import CSVLoader, CSVRow


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


def main() -> None:
    process_example_1()
    process_example_2()


if __name__ == "__main__":
    main()
