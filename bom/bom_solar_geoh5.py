"""Import in solar information from the Australia's BOM into GeoH5 workspace.

* BOM is the Bureau of Meteorology (www.bom.gov.au).
* The solar data can be downloaded from:
  http://www.bom.gov.au/jsp/awap/solar/index.jsp
"""

from __future__ import annotations

import argparse
import pathlib
import typing

from geoh5py.groups import ContainerGroup
from geoh5py.objects import Grid2D
from geoh5py.workspace import Workspace

from bom import read_grid_file, read_solar_exposure_data


__author__ = "Sean Donnellan"
__copyright__ = "Copyright (C) 2025 Sean Donnellan"
__version__ = "1.0.0"


def import_as_grid(
    workspace: Workspace, group: ContainerGroup, contents: typing.IO
) -> Grid2D:
    """Import grid provided by contents into the provide group and workspace.

    group must be a group in the given workspace.
    """
    name = contents.name.replace(".txt.gz", "")
    lower_left_corner, cell_size, data = read_grid_file(contents)
    grid = Grid2D.create(
        workspace,
        u_count=data.shape[1],
        v_count=data.shape[0],
        u_cell_size=cell_size,
        v_cell_size=cell_size,
        origin=[lower_left_corner[0], lower_left_corner[1], 0.0],
        rotation=0.0,  # Degrees, counter clockwise.
        dip=0.0,
        vertical=False,
        name=name,
        parent=group,
    )
    grid.add_data(
        {
            "Solar": {
                "association": "CELL",
                "values": data.to_numpy()[::-1, ::1].ravel(),
            },
        },
    )
    return grid


def import_data_to_grid(workspace: Workspace, contents: typing.IO) -> Grid2D:
    """Import the data (contents) into a 2D Grid within the workspace."""
    grid_name = "Solar - BOM"
    lower_left_corner, cell_size, data = read_grid_file(contents)
    data_origin = [lower_left_corner[0], lower_left_corner[1], 0.0]
    entity = workspace.get_entity(grid_name)[0]
    if entity is None:
        # Create the grid.

        grid = Grid2D.create(
            workspace,
            u_count=data.shape[1],
            v_count=data.shape[0],
            u_cell_size=cell_size,
            v_cell_size=cell_size,
            origin=data_origin,
            rotation=0.0,  # Degrees, counter clockwise.
            dip=0.0,
            vertical=False,
            name=grid_name,
        )
    else:
        if not isinstance(entity, Grid2D):
            raise ValueError(f"{grid_name} is not a grid.")
        grid = entity
        # if grid.origin.tolist() != data_origin:
        #     error = f"Data doesn't align to existing grid: {grid.origin} " + \
        #         f"{data_origin}"
        #     raise ValueError(error)

    data_name = contents.name.replace(".txt.gz", "")
    grid.add_data(
        {
            data_name: {
                "association": "CELL",
                "values": data.to_numpy()[::-1, ::1].ravel(),
            },
        },
    )


def import_solar(
    data_directory: pathlib.Path,
    workspace_path: pathlib.Path,
    *,
    single_grid: bool = False,
) -> None:
    """Import the solar data from data_directory into the given workspace."""

    def create_group_if_missing(workspace: Workspace, name: str) -> ContainerGroup:
        existing_group = next(
            (group for group in workspace.groups if group.name == name),
            None,
        )
        if existing_group:
            return existing_group
        return ContainerGroup.create(workspace, name=name)

    with Workspace.create(workspace_path) as workspace:
        workspace: Workspace
        if workspace.geoh5.mode == "r":
            message = (
                "Workspace is ready-only. "
                + "If it is open in another application close it first."
            )
            raise OSError(message)

        if single_grid:
            read_solar_exposure_data(
                data_directory,
                lambda c: import_data_to_grid(workspace, c),
            )
        else:
            group = create_group_if_missing(workspace, "Solar - BOM")
            read_solar_exposure_data(
                data_directory,
                lambda c: import_as_grid(workspace, group, c),
            )
            workspace.save_entity(group)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import solar data from Australia's Bureau of "
        "Meteorology as a grid.",
    )

    parser.add_argument(
        "--data-directory",
        help="folder containing the data",
        default=pathlib.Path("G:\\GeoData\\Source\\BOM - Australia\\awap"),
        type=pathlib.Path,
    )
    parser.add_argument(
        "--output",
        help="the path and name of the GeoH5 file to create.",
        default=pathlib.Path("bom_solar.geoh5"),
        type=pathlib.Path,
    )
    parser.add_argument(
        "--single-grid",
        help="a single grid will be created and each file will add data to "
        "that grid.",
        action="store_true",
    )
    arguments = parser.parse_args()
    import_solar(
        arguments.data_directory, arguments.output,
        single_grid=arguments.single_grid,
    )
