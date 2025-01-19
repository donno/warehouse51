"""Functions for working with Bureau of Meteorology (Australia) data.

This module can use the third party package "unlzw3" to handle the
decompression of .Z compressed files.

BOM is the Bureau of Meteorology (www.bom.gov.au).
* The solar data can be downloaded from:
  http://www.bom.gov.au/jsp/awap/solar/index.jsp
"""

from __future__ import annotations

import gzip
import io
import os
import pathlib
import tarfile
import typing

# This module uses pandas to read the CSV data into dataframe.
import pandas


__author__ = "Sean Donnellan"
__copyright__ = "Copyright (C) 2021 Sean Donnellan"
__version__ = "0.3.0"


def read_grid_file(contents: typing.IO[bytes]):
    """Read a grid file in ESRI ASCII Grid format.

    A starting point for the format is available on Wikipedia at:
    https://en.wikipedia.org/wiki/Esri_grid
    """
    # ncols         4
    # nrows         6
    # xllcorner     0.0
    # yllcorner     0.0
    # cellsize      50.0
    # NODATA_value  -9999
    # Followed by the values (in the above nrows (6) each with ncolumns (4) per
    # row).

    column_count = contents.readline()
    assert column_count.startswith(b"ncols ")
    row_count = contents.readline()
    assert row_count.startswith(b"nrows ")
    column_count = int(column_count[5:].strip())
    row_count = int(row_count[5:].strip())

    # Next two corners are tre the western (left) x-coordinate and
    # southern (bottom) y-coordinates, such as easting and northing.
    # When the data points are cell-centred xllcenter and yllcenter are used
    # to indicate such registration.
    x_coordinate = contents.readline()
    y_coordinate = contents.readline()

    assert x_coordinate.startswith((b"xllcorner ", (b"xllcenter ")))
    assert y_coordinate.startswith((b"yllcorner ", (b"yllcenter ")))

    align_centre = x_coordinate.startswith(b"xllcenter ")
    if align_centre:
        assert y_coordinate.startswith(
            b"yllcenter ",
        ), "Both coordinates should be corner or centre not a mix."

    x_coordinate = float(x_coordinate[9:].strip())
    y_coordinate = float(y_coordinate[9:].strip())

    cell_size = contents.readline()
    assert cell_size.startswith(b"cellsize ")
    cell_size = float(cell_size[9:].strip())

    nodata_value = contents.readline()
    assert nodata_value.startswith(b"nodata_value ")
    nodata_value = float(nodata_value[13:].strip())

    # print(
    #     f"{column_count} by {row_count} at ({x_coordinate}, {y_coordinate})"
    #     + f" with cell size {cell_size} and no data value of {nodata_value}",
    # )

    data = pandas.read_csv(
        contents,
        sep="\\s+",
        na_values=nodata_value,
        header=None,
        nrows=row_count,
    )

    assert data.shape == (row_count, column_count)

    # Note: pandas doesn't seem to stop, so to read the trailer with
    # contents.readline() is a no go.

    return (x_coordinate, y_coordinate), cell_size, data


def unwrap_data(path: pathlib.Path | str, grid_file_callback):
    """Unwraps the data from a tarball & decompresses it.

    Technically if the path is a tarball, it can contain more than one grid
    file and that is supported however Australia's Bureau of Meteorology does
    not provide data in that form. As such this is untested.

    With the help of the unlzw3 this function can handle the .Z compressed
    files that can be downloaded from:
    - http://www.bom.gov.au/climate/maps/rainfall/
    - http://www.bom.gov.au/jsp/awap/solar/index.jsp

    path: str or os.PathLike
        The path to the file containing the grid.

    grid_file_callback:
        A function that is passed the file-like object containing the contents
        of the grid file. Typically the provided function would call
        read_grid_file().
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(os.fspath(path))

    results = []

    if tarfile.is_tarfile(path):
        with tarfile.open(path) as tar:
            names = tar.getnames()
            names.remove("README")
            for name in names:
                contents = tar.extractfile(name)
                with gzip.GzipFile(filename=name, fileobj=contents, mode="r") as grid:
                    results.append(grid_file_callback(grid))
        return results
    elif path.suffix == ".gz":
        with gzip.GzipFile(path, mode="r") as grid:
            return grid_file_callback(grid)
    elif path.suffix == ".Z":
        try:
            import unlzw3
        except ImportError as error:
            message = "Can't unwrap this data without unlzw3 package."
            raise ImportError(message, error.name, error.path) from None

        with path.open("rb") as reader:
            uncompressed = unlzw3.unlzw(reader.read())
            contents = io.BytesIO(uncompressed)
            contents.name = path.name
            return grid_file_callback(contents)
    else:
        message = f"No support for {path.name}"
        raise NotImplementedError(message)


def read_solar_exposure_data(path: pathlib.Path | str, grid_file_callback):
    """Read teh solar exposure data within path.

    If path is a directory then files matching the known solar exposure files
    will be found and read.
    If path is a file that corresponding it will be attempted to be read.

    This provides the file-like object to grid_file_callback which can then
    be read with via the read_grid_file() function.
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(os.fspath(path))

    tar_name_prefix = "awap_solar_daily_grids"
    single_file_extensions = (".txt", ".txt.gz")
    if path.is_dir():
        for item in path.iterdir():
            if item.name.startswith(tar_name_prefix) and item.suffix == ".tar":
                unwrap_data(item, grid_file_callback)
            elif item.name.startswith("solar.") and item.name.endswith(
                single_file_extensions,
            ):
                # This handles the case if the tar have been extracted.
                unwrap_data(item, grid_file_callback)
    elif path.name.startswith(tar_name_prefix) and item.suffix == ".tar":
        unwrap_data(item, grid_file_callback)
    elif item.name.startswith("solar.") and item.name.endswith(
                single_file_extensions,
            ):
        unwrap_data(item, grid_file_callback)
