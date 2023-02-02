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


def process_example_1():
    print("Processing Example 1")

    with open("csv_examples/example-1.csv") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")

        csv_loader = CSVLoader(
            reader=reader,
            output_model_cls=Example1Row,
            has_header=True,
        )

        models = csv_loader.read_to_models()
        for model in models:
            print(model)


def process_example_2():
    print("Processing Example 2")

    with open("csv_examples/example-2.csv") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")

        csv_loader = CSVLoader(
            reader=reader,
            output_model_cls=Example2Row,
            has_header=True,
        )

        models = csv_loader.read_to_models()
        for model in models:
            print(model)


def test_optionals():
    class TestOptionals(CSVRow):
        just_str: str
        opt_str: Optional[str]

    obj = TestOptionals(
        just_str="abc",
        opt_str="",
    )


def main():
    process_example_1()
    process_example_2()
    # test_optionals()


if __name__ == "__main__":
    main()
