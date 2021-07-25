"""Additional tooling built around HGT files that is not core to reading
the files themselves.
"""

import hgt


def surface_for_tiles(source_folder, elevation):
    """Yields (northing, easting, (points, faces)) where the points and faces
    represent the surface of the tile at the northing and easting for each
    tile in the given folder.

    source_folder
        The directory containing HGT files.
    elevation
        The elevation to use for the tiles, as the provided points will be 3D.

    """
    points = [
        hgt.location_hgt(path) for path in hgt.find_hgt_files(source_folder)]

    for northing, easting in points:
        yield northing, easting, surface_for_tile(northing, easting, elevation)


def surface_for_tile(northing, easting, elevation):
    """Returns the points and faces that represent the tile boundary.
    The provided elevation will be used and thus it will be uniform across the
    tile. The corner points will not be based on the elevation of the corners
    in the tiles nor will it be the average elevation.

    Example
    -------
    Generate a surface for each tile in a folder:

    >>> import hgt
    >>> import hgtools
    >>> points = [
    >>>   hgt.location_hgt(path) for path in hgt.find_hgt_files(source_folder)]
    >>> for northing, easting in points:
    >>>      points, faces = surface_for_tile(northing, easting, 0.0)
    """

    points = [
        (easting, northing, elevation),
        (easting + 1, northing, elevation),
        (easting + 1, northing + 1, elevation),
        (easting, northing + 1, elevation),
    ]

    faces = [
        (0, 1, 2),
        (2, 3, 0),
    ]

    return points, faces
