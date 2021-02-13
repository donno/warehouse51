"""Provides ability to read the HGT file format which is the data file of the
Shuttle Radar Topography Mission (SRTM).

Bring the pieces together to form the reader:
    - To determine the location of a tile use:
      >>> latitude, longitude = hgt.location_hgt(hgt_path)
    - To determine the number of rows and columns.
      >>> size = hgt.size_hgt(hgt_path)
      You may find it useful to use 1/size.
    - Read the values
      >>> for value in hgt.read_hgt(hgt_path):
      Or with  the row and column information:
      >>> for (row, column), height in zip(
            itertools.product(range(size), range(size)),
            hgt.read_hgt(hgt_path)):
"""

__author__ = "Sean Donnellan"
__copyright__ = "Copyright (C) 2020 Sean Donnellan"
__version__ = "0.3.0"

import array
import io
import math
import os
import sys
import typing
import zipfile

NO_DATA_VALUE = -32768

SIZE_TO_STEP = {
    1201: 90,
    3601: 30,
}


def location_hgt(name: str):
    """The location as latitude and longitude based on the filename."""
    if zipfile.is_zipfile(name):
        name = os.path.basename(os.path.splitext(name)[0]).split('_')[-1]
    elif name.endswith('.hgt'):
        name = os.path.basename(os.path.splitext(name)[0])

    if name.startswith(('n', 'N')):
        # North latitude
        if any(c in name for c in ('W', 'w')):
            north, _, westing = name[1:].lower().partition('w')
            return int(north), -int(westing)
        elif any(c in name for c in ('e', 'e')):
            north, _, easting = name[1:].lower().partition('e')
            return int(north), int(easting)
        else:
            raise ValueError('Must be west or east.')
    elif name.startswith(('s', 'S')):
        if any(c in name for c in ('W', 'w')):
            south, _, westing = name[1:].lower().partition('w')
            return -int(south), -int(westing)
        elif any(c in name for c in ('e', 'e')):
            south, _, easting = name[1:].lower().partition('e')
            return -int(south), int(easting)
        else:
            raise ValueError('Must be west or east.')
    else:
        raise ValueError('Must be north or south.')


def size_hgt(path: typing.Union[str, bytes, os.PathLike]):
    """The number of rows & columns in the file at path.

    This will be either 3601 for 1-arc second or 1201 for 3-arc seconds.
    """
    if zipfile.is_zipfile(path):
        name = os.path.basename(os.path.splitext(path)[0]).split('_')[-1]

        with zipfile.ZipFile(path) as hgt_zip:
            return int(math.sqrt(hgt_zip.getinfo(name + '.hgt').file_size / 2))

    return int(math.sqrt(os.stat(path).st_size / 2))


def read_hgt(path: typing.Union[str, bytes, os.PathLike]):
    """Read a HGT (height) file which is a data file of the Shuttle Radar
    Topography Mission (SRTM).

    Details of the format are from the quick start documentation.
        https://dds.cr.usgs.gov/srtm/version2_1/Documentation/Quickstart.pdf

    The filename refers to the latitude and longitude of the lower
    left corner of the tile and is the geometric centre of that lower
    left pixel.

    The contents of the file are a series of signed two-byte integers in
    big-endian order.

    A cell (or pixel as mentioned above) that has no data is known as data
    voids (i.e heights) and have a value of -32768.

    Heights are in meters referenced to the WGS84/EGM96 geoid.

    path
        The path to the HGT file to read.
    """

    height_count = size_hgt(path) ** 2
    # If height_count is 1201 * 1201 then data is sampled at three arc-second
    # (~90m). This also means the file is a SRTM3 file.
    # If height_count is 3601 * 3601 then data is sampled at one arc-second
    # (~30m). This also means the file is a SRTM1 file.

    def _read_hgt_file(contents: typing.IO[bytes]):
        heights = array.array('h')
        heights.fromfile(contents, height_count)

        if sys.byteorder == 'little':
            heights.byteswap()
        return heights

    if zipfile.is_zipfile(path):
        name = os.path.basename(os.path.splitext(path)[0]).split('_')[-1]

        with zipfile.ZipFile(path) as hgt_zip:
            with hgt_zip.open(name + '.hgt', 'r') as hgt_file:
                return _read_hgt_file(hgt_file)
    else:
        with open(path, 'rb') as hgt_file:
            return _read_hgt_file(hgt_file)


def _read_values(path: typing.Union[str, bytes, os.PathLike]):
    file_size = os.stat(path).st_size
    if file_size == 1201 * 1201:
        # Data is sampled at three arc-second (~90m).
        print('File is meta-data file for SRTM3 file like a NUM or SWB')
    elif file_size == 3601 * 3601:
        # Data is sampled at one arc-second (~30m).
        print('File is meta-data file for SRTM1 file like a NUM or SWB')

    with open(path, 'rb') as reader:
        while True:
            height = int.from_bytes(reader.read(1), byteorder='big')
            yield height


def read_num(path: typing.Union[str, bytes, os.PathLike]):
    """Read the contents of the NUM file which indicate number of DEM tiles
    used and the source of the data.

    See https://lpdaac.usgs.gov/products/nasadem_hgtv001/ for more
    information about how to match the values back to a source.

    path
        The path to the NUM file to read.
    """

    for value in _read_values(path):
        yield value


def find_hgt_files(path: typing.Union[str, bytes, os.PathLike]):
    """Return an iterator of HGT file(s) in the given path.

    Path may be a single file in which case the iterator will provide a single
    item to that file."""
    use_directory = os.path.isdir(path)
    if use_directory:
        for entry in os.scandir(path):
            if entry.is_file():
                if entry.name.endswith('.hgt'):
                    yield entry.path
                elif entry.name.endswith('.zip') and '_HGT_' in entry.name:
                    yield entry.path
    else:
        yield path


def _example():
    """A small example used for developing the module."""
    for height in read_hgt('N03W074.hgt'):
        print(height)


if __name__ == '__main__':
    _example()
