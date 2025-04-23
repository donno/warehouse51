"""Static web site generator for the results from an election.

- House of representatives
  - By state/territory
    - By Division
      - By Polling Place
"""

import argparse
import pathlib

import pandas
import jinja2


SCRIPT_DIRECTORY = pathlib.Path(__file__).parent
"""The path to the directory containing this script."""


def from_csv(event_id: int) -> pandas.DataFrame:
    """Load the first preferences by polling place from CSV.

    This is to check that the page generation works, before working on reading
    the data from the original mark-up feeds.

    The CSV file is generated from AEC  Tally Room website at:
    https://results.aec.gov.au/
    """
    source = (
        SCRIPT_DIRECTORY
        / f"HouseStateFirstPrefsByPollingPlaceDownload-{event_id}-SA.csv"
    )

    return pandas.read_csv(source, skiprows=[0])


class PageGenerator:
    """Generate a HTML page from the data given."""

    def __init__(self, event_id: int, output_path_base: pathlib.Path):
        self.env = jinja2.Environment(
            # This would use PackageLoader if this project was converted into
            # a Python package.
            loader=jinja2.FileSystemLoader(SCRIPT_DIRECTORY / "templates"),
            autoescape=jinja2.select_autoescape(),
        )
        self.output_path_base = output_path_base
        """The base path where the the pages should be generated."""

        self.event_id = event_id
        """The ID of the event for tallying."""

        self.output_path_base.mkdir(exist_ok=True)

    def render_polling_place(self, place: dict, candidates: list[dict]):
        """Render the poling place file."""
        template = self.env.get_template("polling_place.html")
        return template.render(
            place=place,
            candidates=candidates,
        )

    def polling_page_path(self, polling_place_id: int) -> pathlib.Path:
        return (
            self.output_path_base
            / f"HousePollingPlaceFirstPrefs-{self.event_id}-{polling_place_id}.html"
        )


def polling_place_page(
    page_generator: PageGenerator, division: str, polling_place: str, results
):
    """Generate the contents for the polling place page limited to a division."""
    polling_place_id = results["PollingPlaceID"].iloc[0]

    # TODO: Ensure the ballot position ordering is honoured. For now
    # assume the source data is already sorted.
    # TODO: Include Two candidate preferred.
    candidates = [
        {
            "name": f"{row.Surname}, {row.GivenNm}",
            "party": row.PartyNm,
            "votes": row.OrdinaryVotes,
            "swing_percent": row.Swing,
        }
        for row in results.itertuples()
    ]

    destination_path = page_generator.polling_page_path(polling_place_id)
    with destination_path.open("w") as writer:
        writer.write(
            page_generator.render_polling_place(
                place={
                    "name": polling_place,
                    "address": "Unknown - not in given data set.",
                },
                candidates=candidates,
            )
        )


def generate_polling_place_site(page_generator: PageGenerator, data: pandas.DataFrame):
    # Determine polling places (if limited by division) or division.
    grouped = data.groupby("PollingPlace")
    for name, group in grouped:
        division = group["DivisionNm"].iloc[0]
        polling_place_page(
            page_generator,
            division,
            name,
            group,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Generate a static web site from election results.",
    )
    parser.add_argument(
        "--destination",
        help="The directory to write the webpage.",
        default=pathlib.Path.cwd() / "output_web",
    )
    parser.add_argument(
        "--event",
        help="The ID of the event.",
        default=27966,
        type=int,
    )

    parser.add_argument(
        "--division",
        help="Limit the generation to a particular division.",
    )

    arguments = parser.parse_args()

    data = from_csv(arguments.event)

    generator = PageGenerator(
        arguments.event,
        arguments.destination,
    )

    if arguments.division:
        data = data[data["DivisionNm"] == arguments.division]
        generate_polling_place_site(generator, data)
    else:
        grouped = data.groupby(["DivisionNm"])
        for name, group in grouped:
            print(name)
            print(group)


if __name__ == "__main__":
    main()
