"""Functions for operating on the APKINDEX.tar.gz from Alpine Linux."""

import tarfile
import pathlib
import os
import itertools
import dataclasses
import argparse


@dataclasses.dataclass
class Package:
    checksum: str
    """The base64 encoded binary hash digest of the control stream from the package.

    The prefix Q1 indicates its the newer digest (post MD5)"""
    name: str
    version: str
    architecture: str
    """The architecture of the package (for example: x86_64)."""
    size: int
    installed_size: int
    description: str
    url: str
    license: str
    origin: str
    build_time: int
    """Unix timestamp of the package build date/time."""
    commit: str
    maintainer: str = ""
    """The name (and typically email) of person who built the package."""
    provider_priority: int = 100
    dependencies: list = dataclasses.field(default_factory=lambda: [])
    provides: list = dataclasses.field(default_factory=lambda: [])
    install_if: list = dataclasses.field(default_factory=lambda: [])

    @classmethod
    def from_lines(cls, lines: list):
        short_form_to_long_name = {
            "C": "checksum",
            "P": "name",
            "V": "version",
            "A": "architecture",
            "S": "size",
            "I": "installed_size",
            "T": "description",
            "U": "url",
            "L": "license",
            "o": "origin",
            "m": "maintainer",
            "t": "build_time",
            "c": "commit",
            "k": "provider_priority",
            "D": "dependencies",
            "p": "provides",
            "i": "install_if",
        }

        integer_keys = {"S", "I", "t", "k"}
        """The set of short form keys that represent integer values."""

        list_keys = {"D", "p"}
        """The set of short form keys that represent list values.

        The values are separated by spaces."""

        def split(line) -> tuple[str, str]:
            """Split the line into key and value."""
            key, _, value = line.decode("utf-8")[:-1].partition(":")
            if key in integer_keys:
                value = int(value)
            elif key in list_keys:
                value = value.split(" ")
            return key, value

        def decode(lines):
            for line in lines:
                yield split(line)

        reformatted = {
            short_form_to_long_name[key]: value for key, value in decode(lines)
        }
        return cls(**reformatted)


def packages(index: os.PathLike | str):
    """Query the packages in the given index file."""

    def end_of_package(line) -> bool:
        return line != b"\n"

    with tarfile.open(index) as tarball:
        index_file = tarball.extractfile("APKINDEX")

        while True:
            parts = itertools.takewhile(end_of_package, index_file)
            lines = list(parts)
            if lines:
                yield Package.from_lines(lines)
            else:
                break


def list_packages(index: os.PathLike | str, verbose: bool = False):
    """Print out the list of packages."""
    for package in packages(index):
        if verbose:
            print(package)
        else:
            print(
                f"{package.name} {package.version} ({package.size} bytes) - {package.description}"
            )


def description(index: os.PathLike | str):
    """Return the description from the index package."""
    with tarfile.open(index) as tarball:
        return tarball.extractfile("DESCRIPTION").read().decode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query Alpine's package index.",
    )
    parser.add_argument(
        "index",
        default=pathlib.Path("APKINDEX.tar.gz"),
        type=pathlib.Path,
        help="The Path to the APINDEX.tar.gz",
        nargs="?",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show additional information",
    )
    arguments = parser.parse_args()
    list_packages(arguments.index, arguments.verbose)
