"""Create names of companies.

This simply uses a list of names from another source.

The three sources I considered were:
* Genus of birds
* Names of prokaryotics
* Names of Australia suburbs - this is what I settled on.

TODO
----
* Add option to customise the names to add a prefix or suffix such as
  "Brothers" or "And Co" or "Limited".
"""

import enum
import collections
import csv
import dataclasses
import io
import pathlib
import random
import zipfile


class UserNameStyle(enum.Enum):
    """The style of user name's at a given company."""

    FIRST_DOT_LAST = 1
    """first_name.last_name"""

    F_LAST = 2
    """First letter of first name and full last name"""

    F_3_DOT_LAST = 3
    """Up to first three characters for first name and full last name."""

    FOUR_AND_FOUR = 4
    """Up to first four characters for first name and first four of last name."""

    EMPLOYEE_ID = 5
    """Assign the employee a number and use that."""

    def __repr__(self):
        return self.name


@dataclasses.dataclass
class Company:
    name: str
    """The name of the company."""

    domain: str
    """The domain name for the company."""
    # TODO This may be derived instead for company name, or it might need a
    # domain name style to decide it.

    user_name_style: UserNameStyle
    """The style of the usernames at the company.

    This with the domain is used to determine the email address of an employee.
    """

    head_count: int = 0
    """The number of people employed by the company."""

    def email_for_user(self, first_name: str, last_name: str, employee_id: int) -> str:
        """Generate email for a given user.

        The caller will need to check if there are two people with same
        email and generate unique name for the subsequent people.

        Examples
        --------
        >>> args = ["John", "Smith", 1234]
        >>> Company("test", "test.example", UserNameStyle.FIRST_DOT_LAST).email_for_user(*args)
        'john.smith@test.example'
        >>> Company("test", "test.example", UserNameStyle.F_LAST).email_for_user(*args)
        'jsmith@test.example'
        >>> Company("test", "test.example", UserNameStyle.F_3_DOT_LAST).email_for_user(*args)
        'joh.smith@test.example'
        >>> Company("test", "test.example", UserNameStyle.FOUR_AND_FOUR).email_for_user(*args)
        'johnsmit@test.example'
        >>> Company("test", "test.example", UserNameStyle.EMPLOYEE_ID).email_for_user(*args)
        'e1234@test.example'
        """
        first_name = first_name.replace(" ", "_")
        last_name = last_name.replace(" ", "_").replace("'", "")
        match self.user_name_style:  # Historic moment - my first match in Py.
            case UserNameStyle.FIRST_DOT_LAST:
                return f"{first_name}.{last_name}@{self.domain}".lower()
            case UserNameStyle.F_LAST:
                return f"{first_name[0]}{last_name}@{self.domain}".lower()
            case UserNameStyle.F_3_DOT_LAST:
                return f"{first_name[:3]}.{last_name}@{self.domain}".lower()
            case UserNameStyle.FOUR_AND_FOUR:
                return f"{first_name[:4]}{last_name[:4]}@{self.domain}".lower()
            case UserNameStyle.EMPLOYEE_ID:
                return f"e{employee_id}@{self.domain.lower()}"
        raise NotImplementedError


def adjust_name(name: str) -> str:
    """Adjust the name to remove unwanted artifacts.

    For example:
        "ACT Remainder - " in "ACT Remainder - Cotter River".
        (State) i.e. " (ACT)"
    """
    name = name.partition("(")[0]
    before, _, after = name.partition(" - ")
    return (after or before).strip()


def state_suburbs():
    """Return the names and area (KM^2) of suburbs in Australia.

    The data is State Suburbs ASGS Edition 2016 in .csv Format
    The data is licenced under the Creative Commons Attribution 2.5 Australia.
    The data source is: https://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/1270.0.55.003July%202016?OpenDocument
    """
    archive_path = pathlib.Path(__file__).parent / "1270055003_ssc_2016_aust_csv.zip"
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            path = pathlib.PurePath(info.filename)
            if path.suffix != ".csv":
                continue

            with io.TextIOWrapper(
                archive.open(info, "r"),
                encoding="utf-8",
            ) as reader:
                csv_reader = csv.DictReader(reader)
                for record in csv_reader:
                    yield record["SSC_NAME_2016"], float(record["AREA_ALBERS_SQKM"])


def merge_state_suburbs():
    """Return the names and area of suburbs in Australia, without duplicates.

    Duplicates are merged together.
    """
    counter = collections.Counter()
    for name, area in state_suburbs():
        counter[adjust_name(name)] += int(area * 10**6)  # Square meters.
    return counter.items()


def generate_company_names(n: int) -> list[str]:
    """Generate the names of a given number of companies (n).


    Limitations
    -----------
    * This pulls names from an existing list as such n must be smaller than that
      source list.
    * Names won't be industry specific due to the source dat.a
      Maybe one day it will be expanded to do that, such as including particular
      industries i.e. "Larry's Fruit Pickers". More likely, in the short term
      it more likely to be extended so you can provide a customise_name function
      to add to the start or end.
    """

    # The original idea was to use the area of the suburb to determine the
    # the size of the company but that was just to wide ranging.
    choices = [
        name
        for name, area in merge_state_suburbs()
        if area > 0 and " of " not in name
    ]
    return random.choices(choices, k=n)


def name_to_domain(name: str) -> str:
    """Convert a company name to a domain.

    This should possibly have option to control the top-level domain  / country
    and/or use a vanity domain, e.g. .dev, .ai, .shop etc.

    What would be better is country code with list of how many usages there are
    to use for using as a weighting. Something like
    https://domainnamestat.com/statistics/tldtype/country but open.
    https://netapi.com/lists-cctld-domains/

    See https://data.iana.org/TLD/tlds-alpha-by-domain.txt
    """
    return f'{name.lower().replace(" ", "")}.example'


def generate_companies(n: int) -> list[Company]:
    """Generate companies of a given number (n)."""
    names = generate_company_names(n)

    # Make EMPLOYEE_ID a rare option, as its is rather strange.
    weights = [1 if style is UserNameStyle.EMPLOYEE_ID else 500
               for style in UserNameStyle]
    username_styles = random.choices(list(UserNameStyle), weights=weights, k=n)

    return [
        Company(
            name=name,
            # Assume this is international.
            domain=name_to_domain(name),
            user_name_style=style,
            head_count=0,  # Didn't end up making this part of this module.
        )
        for name, style in zip(names, username_styles)
    ]


if __name__ == "__main__":
    for company in generate_companies(10):
        print(company)
