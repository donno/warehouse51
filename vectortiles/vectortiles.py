"""Read from MBTiles file..

The name likely comes from Mapbox Tiles given that Mapbox produced the
format and its specification.

Within the MBTiles file this module expects vector tile rather than raster
files.

To read vector tiles this needs the package `protobuf` installed.

The specification is:
https://github.com/mapbox/vector-tile-spec/blob/master/2.1%2Fvector_tile.proto

Sample data can be found here:
    https://wiki.openstreetmap.org/wiki/MBTiles

"""

__author__ = "Sean Donnellan"
__copyright__ = "Copyright (C) 2022 Sean Donnellan"
__version__ = "0.2.0"

import argparse
import gzip
import itertools
import os.path
import sqlite3
import vector_tile_pb2

GZIP_HEADER = b'\x1f\x8b\x08'

"""
NOTES

Layers
  water
  waterway
  landcover
  landuse
  mountain_peak
  park
  boundary
  aeroway
  transportation
  building
  water_name
  transportation_name
  place
  housenumber
  poi


Tile (0,0,0) has:
    water
    landcover
    boundary
    water_name
    place
"""

# Define a type alias for the geometry type enumeration from the protocol
# buffer specification.
GeometryType = vector_tile_pb2.Tile.GeomType
GeometryType.__doc__ = "Enumeration that represents the type of geometry " + \
    "stored in a feature."""


class MBTiles:
    """Open and read from a mbtiles file.

    This class can be used as a context manager.

    The file is a sqlite3 database with at least these tables:
    - metadata
    - tiles

    There are other tables but they are unused at this time.

    TODO: Provide operations for querying zoom levels and coordinates.
    """
    def __init__(self, filename : str):
        """Open a mbtiles file.

        Parameters
        ----------
        filename
            The path to the mbtiles file to read.
        """
        if os.path.isfile(filename):
            self._database = sqlite3.connect(filename)
        else:
            self._database = None
            raise FileNotFoundError(f'No MBTiles file found at {filename}')

        self._cursor = self._database.cursor()

        # Read the metadata.
        self._cursor.execute("SELECT name, value from metadata")
        self.meta = {row[0]: row[1] for row in self._cursor.fetchall()}

    def tile(self, z: int, x: int, y: int):
        """Return the tile at z, x, y.

        Parameters
        ----------
        z
            The zoom level
        x
            The tile's x-coordinate
        y
            The tile's y-coordinate

        Returns
        -------
        bytes
            The data for the tile in bytes.
        """
        self._cursor.execute(
            "SELECT tile_data FROM tiles "
            "WHERE zoom_level=? AND tile_column=? AND tile_row=? "
            "LIMIT 1",
            (z, x, y),
        )

        row = self._cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def close(self):
        """Close the file."""
        self._cursor.close()
        self._database.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def pairwise(iterable):
    """Return successive overlapping pairs taken from the input iterable.

    pairwise('ABCDEFG') --> AB BC CD DE EF FG

    This function is available in itertools as of Python 3.10.
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    a = iter(iterable)
    return zip(a, a)


def read_vector_tile(source_data):
    """Read the tile from the source data.

    If the source data is compressed with GZIP it will be decompressed first.

    It is expected the tile will be a vector tile in protocol buffer format
    according to the vector_tile.proto.

    A .mbtiles file can contain raster tiles instead.
    """
    if source_data.startswith(GZIP_HEADER):
        source_data = gzip.decompress(source_data)

    decoded_tile = vector_tile_pb2.Tile()
    decoded_tile.ParseFromString(source_data)
    return decoded_tile


def parse_geometry(geometry: list):
    """Parses the geometry command stream from the vector tile specification.

    This yields the commands.

    For more information about this see: 4.3 Geometry Encoding from:
        https://github.com/mapbox/vector-tile-spec/tree/master/2.1
    """

    # My first implementation of this from 2019-01-09 did things differently:
    # - It used iter() and next() rather than pop().
    # - It yield a tuple of the CommandType enumeration and the parameters.
    # - It used a function go from from command type to parameter count.
    # - It collected up all the parameters for all the repeated commands and
    #   then divided them into separate lists.

    class MoveToCommand:
        command_id = 1
        parameter_count = 2

        def __init__(self, dx, dy):
            self.dx = dx
            self.dy = dy

        def __repr__(self):
            return f'MoveTo({self.dx}, {self.dy})'

    class LineToCommand:
        command_id = 2
        parameter_count = 2

        def __init__(self, dx, dy):
            self.dx = dx
            self.dy = dy

        def __repr__(self):
            return f'LineTo({self.dx}, {self.dy})'

    class ClosePathCommand:
        command_id = 7
        parameter_count = 0

        def __repr__(self):
            return 'ClosePath()'

    command_types = [MoveToCommand, LineToCommand, ClosePathCommand]

    def decode_zigzag_integer(value):
        return (value>> 1) ^ (-(value & 1))

    while geometry:
        command = geometry.pop(0)
        command_id = command & 0x7
        count = command >> 3

        assert count >= 1

        command_type = next(
            (command_type for command_type in command_types
            if command_id == command_type.command_id), None)

        if command_type is None:
            raise ValueError(f'Unexpected command ID ({command_id}).')

        for _ in range(count):
            parameters = [
                decode_zigzag_integer(parameter)
                for parameter in geometry[:command_type.parameter_count]
            ]
            del geometry[:command_type.parameter_count]
            yield command_type(*parameters)


def process_tile(tile: vector_tile_pb2.Tile):
    # TODO: This function is still a work in-progress. I haven't settled on how
    # I am planning on exposing the tile information.

    # A layer has the properties: version, name, features, keys, values and
    # extent.
    #
    # keys and values form a dictionary / mapping.

    # Example of keys and values:
    # key: class  value: lake (type: string)
    for layer in tile.layers:
        print(f'{layer.name} - v{layer.version}')

        # print(layer.keys)
        # print(layer.values)

        for feature in layer.features:
            if feature.type == GeometryType.POINT:
                print('Point')
            elif feature.type == GeometryType.POLYGON:
                print('Polygon')
            elif feature.type == GeometryType.LINESTRING:
                print('Polyline')
            else:
                raise ValueError(f'Unexpected feature type: {feature.type}')

            geometry = parse_geometry(feature.geometry)

            # feature.tags refers to the dictionary (keys/values) in the layer.
            #
            # The tags are encoded as a repeated pair of integers.
            #
            # A value could be JSON value but with five numerical types instead
            # of one.
            # TODO: Handle the feature tags.

            for k, v in pairwise(feature.tags):
                print('key:', layer.keys[k], 'value:', layer.values[v])

        break

if __name__ == '__main__':
    # A hardcoded default to make developing easier for myself.
    SOUTH_KOREA = r'G:\GeoData\Source\OpenStreetMap\derived\S_Korea.mbtiles'

    parser = argparse.ArgumentParser(
        description='Read data from a vector tile in a MBTiles file.',
        )
    parser.add_argument(
        'mbtiles',
        nargs='?',
        help='The path to the mbtiles file.',
        default=SOUTH_KOREA)

    arguments = parser.parse_args()

    with MBTiles(arguments.mbtiles) as src:
        print(src.meta)
        assert src.meta['format'] == 'pbf'
        tile = src.tile(z=13, x=6987, y=5010)
        process_tile(read_vector_tile(tile))
