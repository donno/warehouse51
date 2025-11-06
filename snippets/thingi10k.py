"""Module for working with thingi10k.

This module works with the a summary of the data in the data set and may
provide tools working with the data set (the large tar).

The original plan was to use the Python package "thingi10k". That was not
suitable, however that simply downloads the entire tar anyway. I was hoping it
would at least let you read the index with out then I could decide what to do
from there.

The metadata files are:
- input_summary.csv - This provides thing ID and licence
- contextual_data.csv - This provides the author.

The data itself can be found at:
https://huggingface.co/datasets/Thingi10K/Thingi10K/resolve/main/Thingi10K.tar.gz
"""

import collections.abc
import csv
import pathlib
import typing
import urllib.request

WORKING_DIRECTORY = pathlib.Path.cwd()

ThingRecord = typing.TypedDict(
    "ThingRecord",
    {
        "ID": str,
        "Thing ID": str,
        "License": str,
        "Link": str,
        "No duplicated faces": bool,
        "Closed": bool,
        "Edge manifold": bool,
        "No degenerate faces": bool,
        "Vertex manifold": bool,
        "Single Component": bool,
        "PWN": bool,
    },
)


def things(
    cache: pathlib.Path = WORKING_DIRECTORY,
    filter_out: collections.abc.Callable[[ThingRecord], bool] | None = None,
) -> collections.abc.Generator[ThingRecord, None, None]:
    """List of the things.

    If filter_out is not None then if it returns True for a given thing it
    then it won't be yield, i.e. it will be filtered out.
    """
    csv_path = cache / "Thingi10K_input_summary.csv"

    if not csv_path.exists():
        urllib.request.urlretrieve(
            "https://huggingface.co/datasets/Thingi10K/Thingi10K/raw/main/metadata/input_summary.csv",
            csv_path,
        )

    # Convert boolean fields from string to booleans.
    boolean_field_names = {
        field_name
        for field_name, field_type in ThingRecord.__annotations__.items()
        if issubclass(field_type, bool)
    }

    with csv_path.open("r") as reader:
        for record in csv.DictReader(reader):
            # Replace boolean fields.
            record.update(
                {
                    field_name: value == "TRUE"
                    for field_name, value in record.items()
                    if field_name in boolean_field_names
                },
            )

            if filter_out(record):
                continue

            yield record


def non_commerical_use(thing: ThingRecord) -> bool:
    """Return true if the thing should be excluded."""
    licence = thing["License"]
    if licence == "unknown_license":
        return True  # Use for commerical purpose is therefore also unknown.
    return "Non-Commercial" in licence or "GNU".startswith(licence)


def not_public_domain(thing: ThingRecord) -> bool:
    """Return true if the thing is not in the public domain."""
    return "Public Domain" not in thing["License"]


def extraction_list(
    things: collections.abc.Iterable[ThingRecord],
) -> collections.abc.Generator[str, None, None]:
    """Generate an extraction list for tar's --files-from feature.

    If the resulting list is saved to extraction.list then this can
    be used with tar like so:
        tar xf Thingi10K.tar.gz --files-from extraction.list
    """
    for thing in things:
        yield f"Thingi10K/raw_meshes/{thing['ID']}.stl"


# TODO: Add function for a rename list so it uses the filename from 'Link'


if __name__ == "__main__":
    with open("extraction.list", "w") as writer:
        for item in extraction_list(things(filter_out=not_public_domain)):
            writer.write(item)
            writer.write("\n")
    print("tar xf Thingi10K.tar.gz --files-from extraction.list")
