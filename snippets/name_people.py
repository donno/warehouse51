""""Create the names of several people.

The data files are not checked in and are not automatically downloaded at this
time.
"""

import collections
import csv
import io
import itertools
import pathlib
import random
import zipfile


def adjust_name_style(name):
    """Adjust the style of a name including its casing and adding '

    Names starting with O <SOMETHING> will become O'<Something>
    Names starting with MC <SOMETHING> will become Mc<Something>
    """
    if name.endswith(" ?"):
        name = name[:-2]
    if name.startswith("?"):
        name = name[1:]
    if name.startswith("MC "):
        return "Mc" + name[3:].title()
    if name.startswith("O "):
        return "O'" + name[2:].title()
    return name.strip("'").title()


def from_popular_baby_names() -> collections.Counter:
    """Return set of first names only based on popular baby names.

    This data comes from popular baby names in the state of South Australia
    from 1944 to 2013.

    The data is licenced under the Creative Commons Attribution.
    The data source is: https://data.sa.gov.au/data/dataset/popular-baby-names

    The data is formatted into names and usage.
    """

    counter = collections.Counter()

    archive_path = pathlib.Path(__file__).parent / "baby-names-1944-2013.zip"
    if not archive_path.is_file():
        archive_path = pathlib.Path.cwd() / archive_path.name

    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            path = pathlib.PurePath(info.filename)
            if path.suffix == ".csv":
                with io.TextIOWrapper(
                    archive.open(info, "r"), encoding="utf-8"
                ) as reader:
                    csv_reader = csv.DictReader(reader)
                    for record in csv_reader:
                        if record["Given Name"] in ("UNNAMED", "(NOT"):
                            continue

                        name = adjust_name_style(record["Given Name"])
                        counter[name] += int(record["Amount"])

    return counter


def surnames(adjust_style: bool = True) -> collections.Counter:
    """Return surnames of people who passed away between 1880 and 1923.

    This data comes from deceased estate files of the state of New South Wales
    from 1880 to 1923.

    The data is licenced under the Creative Commons Attribution.
    The data source is:
        https://data.nsw.gov.au/data/dataset/deceased-estate-files-1880-1923
    """

    counter = collections.Counter()

    csv_path = pathlib.Path(__file__).parent / "deceased-estates.csv"
    if not csv_path.is_file():
        csv_path = pathlib.Path.cwd() / csv_path.name

    with csv_path.open("r", encoding="utf-8") as reader:
        csv_reader = csv.DictReader(reader)
        for record in csv_reader:
            surname = record["Surname"]
            if adjust_style:
                surname = adjust_name_style(surname)
            if surname:
                counter[surname] += 1
    return counter


class NameGenerator:
    """Represent names along with a weighting."""
    def __init__(self, source: collections.Counter):
        names, weights = zip(*source.items(), strict=True)
        self.names = names
        self.cumulative_weights = list(itertools.accumulate(weights))

    def choose(self, k: int = 1) -> list[str]:
        """Random choose a name or k names."""
        return random.choices(self.names, cum_weights=self.cumulative_weights,
                              k=k)


def generate_user_names(n: int):
    """Generate the names of a given number of users (n)."""
    first_names = NameGenerator(from_popular_baby_names())
    last_names = NameGenerator(surnames())

    return zip(first_names.choose(n), last_names.choose(n))


def generate_users(n: int):
    """Generate the given number of users (n)."""
    for first, last in generate_user_names(n):
        print(first, last)


if __name__ == "__main__":
    generate_users(10)
