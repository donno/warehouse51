"""Generate company, groups and users.

Create fictional
- Company / Organisation
- Groups / Departments / Roles
- Users / Employees

Components
----------
Company
* Name
* Domain
* User name style
* Head count

Users
* First name
* Last Name
* Email - derived from their company's user name style and domain.

Group
* Name

Linking
* Group and Company
* User and Company
* User and Group

Output Format

{
  "companies": [
     <company>
  ]
}

Where company is: (See CompanyJson)
{
   "name":
   "domain":
   "groups": [],
   "employees": [
       <employee>
   ]
}

Where employee is: (See EmployeeJson)
{
    "first": "John",
    "last": "Smith",
    "email": "john.smith@company.example",
    "groups": ["management"],
}
"""

import argparse
import bisect
import collections
import itertools
import json
import random
import typing

from name_people import generate_user_names
from name_company import Company, generate_companies


# Ideally, this should cover more "role" and "department", but for now lets go
# with this simplified view.
GROUPS_BY_SIZE = {
    30: [
        ("senior", 2), ("manager", 2), ("clerk", 16),
    ],
    50: [
        ("junior", 8), ("specialist", 10), ("senior", 4), ("manager", 3),
    ],
    200: [
        ("junior generalist", 20),
        ("specialist A", 10),
        ("specialist B", 10),
        ("specialist C", 10),
        ("specialist D", 10),
        ("senior specialist A", 4),
        ("senior specialist B", 4),
        ("senior specialist C", 4),
        ("senior specialist D", 4),
        ("department head A", 2),
        ("department head B", 2),
        ("department head C", 2),
        ("department head D", 2),
        ("head of operations", 6),
        ("team manager", 5),
        ("executive manager", 3),
    ],
}

class EmployeeJson(typing.TypedDict):
    """Represent an employee in JSON as a Python dictionary."""

    first_name: str
    last_name: str
    email: str
    group: list[str]
    """The name of the groups that the employee is a part of at their company.
    """


class CompanyJson(typing.TypedDict):
    """Represent the company in JSON as a Python dictionary."""

    name: str
    """The name of the company."""

    domain: str
    """The domain name for the company."""

    user_name_style: str
    """The name of the style for the user names as used in the emails."""

    employees: list[EmployeeJson]
    """The employees that work at the company."""

    groups: list[str]
    """The name of the groups (or roles) used at the company."""


def expand(opening_range, repeat_count: int) -> list[int]:
    """Expand the range by repeating each element by the given repeat count.

    Examples
    --------
    >>> expand(range(3), 2)
    [0, 0, 1, 1, 2, 2]
    >>> expand(range(3), 3)
    [0, 0, 0, 1, 1, 1, 2, 2, 2]
    >>> expand(range(4), 3)
    [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3]
    >>> expand('ABC', 2)
    ['A', 'A', 'B', 'B', 'C', 'C']
    """

    def _generate():
        for item in opening_range:
            yield from itertools.repeat(item, repeat_count)

    return list(_generate())


def assign_people_to_company(company_count: int, employee_count: int) -> list[int]:
    """Assign people as employees to an company.

    The resulting list is a mapping from the employee to the company based
    on index (i.e. result[0] means employee 0 is at company[0].
    """
    small_company_count = int(0.4 * company_count)
    medium_company_count = int(0.5 * company_count)
    huge_company_count = int(0.1 * company_count)

    minimum_employees_assigned = (
        5 * small_company_count + 50 * medium_company_count + 200 * huge_company_count
    )

    # Take an extra 500 people out to assign to the largest company to give
    # them an extra edge so there least one company bigger than the rest.
    reserved_for_largest_company = 500
    spare = employee_count - minimum_employees_assigned - reserved_for_largest_company

    if spare < 0:
        raise ValueError(
            "Either too many companies, too few people or weighting are off."
        )

    # Some of the companies need more chance then other to get extra employees,
    # otherwise, they all end up equally getting same number, specially the huge
    # companies.
    #
    # Two ways to try:
    # 1) Random
    # 2) Force it to be incremental e. go from 200 to 2000 in increments of 200.
    #    The problem with this you need enough weights for each company, so you
    #    need to repeat it or cycle it.
    company_weights = []
    company_weights.extend(
        random.choices(
            range(-10, 400, 80),
            k=small_company_count,
        ),
    )
    company_weights.extend(
        random.choices(
            range(100, 900, 300),
            k=medium_company_count,
        ),
    )
    company_weights.extend(
        random.choices(
            range(20, 5000, 1000),
            k=huge_company_count,
        ),
    )
    spare_assignment = random.choices(
        range(company_count),
        weights=company_weights,
        k=spare,
    )

    # This is where it is a shame there isn't a aversion of range which takes a
    # start and count. Lets make one.
    sized_range = lambda start, count: range(start, start + count)

    small_company_assignment = expand(range(small_company_count), 5)
    medium_company_assignment = expand(
        sized_range(small_company_count, medium_company_count),
        50,
    )
    huge_company_assignment = expand(
        sized_range(
            small_company_count + medium_company_count,
            huge_company_count,
        ),
        200,
    )

    largest_company = collections.Counter(huge_company_assignment).most_common(1)[0][0]
    largest_company_extra_assignments = list(
        itertools.repeat(
            largest_company,
            reserved_for_largest_company,
        ),
    )

    return (
        small_company_assignment
        + medium_company_assignment
        + huge_company_assignment
        + spare_assignment
        + largest_company_extra_assignments
    )


def assign_people_to_groups(head_count: int) -> list[str]:
    """Assign employees to the company to groups essentially a role.."""
    size_to_groups = list(GROUPS_BY_SIZE.items())
    group_index = bisect.bisect_left(
        size_to_groups, head_count, key=lambda item: item[0],
    )
    group_index = min(group_index, len(GROUPS_BY_SIZE) - 1)
    print('Group index', group_index)
    group_for_size = size_to_groups[group_index][1]
    print(group_for_size)
    names, weights = zip(*group_for_size)
    print(weights)
    return random.choices(names, weights=weights, k=head_count)


def new_parser() -> argparse.ArgumentParser:
    """Return an argument parser for tool for generating users."""
    parser = argparse.ArgumentParser(description="Generate user information.")
    parser.add_argument(
        "--users",
        type=int,
        default=1000,
        help="Number of users to generate.",
    )
    parser.add_argument(
        "--companies",
        type=int,
        default=10,
        help="Number of users to generate.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the information as JSON.",
    )
    return parser



def generate_full_description(
    companies: list[Company],
    users: list[tuple[str, str]],
) -> dict[str, list[CompanyJson]]:
    """Generate a full description of the users, company and groups.

    The resulting dict is JSON-compatible.
    """
    person_to_company = assign_people_to_company(arguments.companies, arguments.users)

    company_to_people = {}
    for person_index, company_index in enumerate(person_to_company):
        # Since the mapping is not done separately, rather than use index like
        # below, sub in the actual user.
        # company_to_people.setdefault(company_index, []).append(person_index)
        company_to_people.setdefault(company_index, []).append(users[person_index])

    company_to_groups_for_people = {}
    for company_index, people in company_to_people.items():
        company_to_groups_for_people[company_index] = assign_people_to_groups(
            len(people),
        )

    def convert_person(
        first_name: str,
        last_name: str,
        company: Company,
        group: str,
    ) -> EmployeeJson:
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": company.email_for_user(first_name, last_name, 0),
            "groups": [group],
        }

    def make_email_unique(company: CompanyJson):
        """Check if emails for employees are unique and make them so if not.

        This is performed in-place.
        """
        seen_emails = set()
        for employee in company["employees"]:
            email = employee["email"]
            while email in seen_emails:
                local_part, _, host = email.partition("@")
                extra = random.randint(10, 200)
                email = f"{local_part}{extra}@{host}"
                employee["email"] = email
            seen_emails.add(email)

    def convert_company(company: Company,
                        employees: list,
                        employee_to_groups: list[str]) -> CompanyJson:
        company: CompanyJson = {
            "name": company.name,
            "domain": company.domain,
            "user_name_style": company.user_name_style.name,
            "groups": list(set(employee_to_groups)),
            "employees": [
                convert_person(first_name, last_name, company, group)
                for (first_name, last_name), group in zip(employees,
                                                          employee_to_groups)
            ],
        }
        make_email_unique(company)
        return company

    return {
        "companies": [
            convert_company(company, company_to_people[index],
                            company_to_groups_for_people[index])
            for index, company in enumerate(companies)
        ],
    }


if __name__ == "__main__":
    parser = new_parser()
    arguments = parser.parse_args()
    user_names = list(generate_user_names(arguments.users))
    companies = generate_companies(arguments.companies)

    if arguments.json:
        print(json.dumps(generate_full_description(companies, user_names), indent=2))
    else:
        print("Companies")
        print("=========")
        for company in companies:
            print(f"  {company}")

        print("Users")
        print("=====")
        for names in user_names:
            print(*names)
