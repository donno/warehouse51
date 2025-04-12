"""Extract a subset of dynamic link libraries based on one's dependencies.

Using Dependencies by lucasg find dependencies of a set of DLLs.

This is intended to be used when several higher level DLLs are present.

For example if given libpng.dll then both libpng.dll and zlib.dll will be
copied to the destination directory assuming zlib was dynamically linked rather
than statically linked.
"""

import shutil
import pathlib
import argparse

import dll_dependencies


def extract(
    source: pathlib.Path,
    destination: pathlib.Path,
    work_directory: pathlib.Path,
):
    depends = dll_dependencies.find_dependencies([source], work_directory)
    destination.mkdir(exist_ok=True)
    for library in depends.nodes:
        shutil.copyfile(
            source.parent / library,
            destination / library,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "source",
        type=pathlib.Path,
        help="The path to a DLL to extract subset from. This should contain its dependencies.",
    )
    parser.add_argument(
        "destination",
        type=pathlib.Path,
        help="The path to copy the DLL and its dependencies to.",
    )
    parser.add_argument(
        "--work-directory",
        type=pathlib.Path,
        help="The path where tools will be extracted.",
        default=dll_dependencies.WORK_DIRECTORY,
    )

    arguments = parser.parse_args()
    extract(arguments.source, arguments.destination, arguments.work_directory)
