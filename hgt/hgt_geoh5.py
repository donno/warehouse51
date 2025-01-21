"""Converts a HGT (height) file which is a data file of the Shuttle Radar
Topography Mission (SRTM) to a Grid2D object in the GEOH5 format.

- This leverages the geo5py package.
- This is not going to be useful in Geoscience ANALYST in its current form
  because the Coordinate System Transformation option is only available in
  Geoscience ANALYST Pro to shift it from WGS84 to a cartesian coordinate.
    - A conversion may be applied by this script in the near future.
"""

from __future__ import annotations


import argparse
import logging
import os
import pathlib

from geoh5py.groups import ContainerGroup
from geoh5py.objects import Grid2D
from geoh5py.workspace import Workspace

import hgt
import hgt_numpy

__author__ = "Sean Donnellan"
__copyright__ = "Copyright (C) 2025 Sean Donnellan"
__version__ = "1.0.0"


def convert_hgt_to_grid(
    workspace: Workspace,
    group: ContainerGroup,
    hgt_path: str | bytes | os.PathLike,
) -> Grid2D:
    """Convert the given HGT to a Grid@D object in the given workspace in group."""
    size = hgt.size_hgt(hgt_path)
    latitude, longitude = hgt.location_hgt(hgt_path)
    grid_name = os.path.splitext(os.path.basename(hgt_path))[0]
    logging.info(
        'Converting HGT "%s"  as "%s" grid in "%s"',
        hgt_path,
        grid_name,
        group.name,
    )
    grid = Grid2D.create(
        workspace,
        u_count=size,
        v_count=size,
        u_cell_size=1.0 / size,
        v_cell_size=1.0 / size,
        origin=[latitude, longitude, 0.0],
        rotation=0.0,
        dip=0.0,
        vertical=False,
        name=grid_name,
        parent=group,
    )
    grid.coordinate_reference_system = {
        "Code": "EPSG:4326",
        "Name": "WGS 84",  # World Geodetic System 1984
    }

    data = hgt_numpy.read_hgt_heights_2d(hgt_path).ravel()
    grid.add_data(
        {
            "Elevation": {
                "association": "CELL",
                # The data is converted from integer to float such that it can
                # be used as a deformation.
                "values": data.astype(float),
            },
        },
    )

    # TODO: Alter the visibility.to hide no-data cells:
    #  elevation != hgt.NO_DATA_VALUE

    return grid


def main(workspace_path: pathlib.Path, path: str | bytes | os.PathLike) -> None:
    """
    Convert the HGT file or files at/in path to Grid2D objects in a workspace.

    If path is a directory then all HGT files in the directory will be
    imported.

    If path is a file then it is assumed that is the path to a HGT file.
    """

    def create_group_if_missing(workspace: Workspace, name: str) -> ContainerGroup:
        existing_group = next(
            (group for group in workspace.groups if group.name == name),
            None,
        )
        if existing_group:
            return existing_group
        return ContainerGroup.create(workspace, name=name)

    with Workspace.create(workspace_path) as workspace:
        group = create_group_if_missing(workspace, "NASADEM - Grids")
        hgt_files = hgt.find_hgt_files(path)
        for hgt_file in hgt_files:
            convert_hgt_to_grid(workspace, group, hgt_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert HGT to Grid2D in GEOH5 workspace.",
    )

    parser.add_argument(
        "path",
        help="folder containing the data or a file.",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--output",
        help="the path and name of the GEOH5 file to create.",
        default=pathlib.Path("nasadem.geoh5"),
        type=pathlib.Path,
    )
    parser.add_argument(
        "--overwrite",
        help="overwrite the GEOH5 file (output) if it already exists.",
        action="store_true",
    )
    arguments = parser.parse_args()
    if arguments.overwrite and arguments.output.exists():
        arguments.output.unlink()
    main(arguments.output, arguments.path)
