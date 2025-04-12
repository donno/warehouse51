"""Parses the output of "dumpbin /exports".

Alternative
-----------
This is recommended instead of using this tool.

  Use Dependencies by lucasg.
    Dependencies.exe -json -exports example.dll

Usage
-----
dumpbin /exports example.dll > example.txt
dumpbin_parser.py example.txt
"""

import pathlib
import enum
import dataclasses
import argparse

@dataclasses.dataclass
class Export:
    ordinal: int
    hint: str
    rva: int
    name: str


def exports(path: pathlib.Path):
    """Parse the exports from Microsoft dumpbin tool"""
    class ParserState(enum.Enum):
        BEFORE_EXPORTS = 0
        DURING_EXPORTS = 1
        AFTER_EXPORTS = 2

    state = ParserState.BEFORE_EXPORTS

    with path.open() as reader:
        for line in reader:
            if state == ParserState.BEFORE_EXPORTS:
                if line.lstrip().startswith("ordinal hint RVA"):
                    state = ParserState.DURING_EXPORTS
            elif state == ParserState.DURING_EXPORTS:
                if line.startswith("  Summary"):
                    state = ParserState.AFTER_EXPORTS
                elif line != "\n":
                    parts = line[:-1].split()
                    yield Export(
                        ordinal=int(parts[0]),
                        hint=parts[1],
                        rva=int(parts[2], 16),
                        name=' '.join(parts[3:]),
                        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        type=pathlib.Path,
        help="The path to a dumpbin /export output",
    )

    arguments = parser.parse_args()
    for export in exports(arguments.source):
        print(export)
