"""Provides utilities for working with HGT files and uses numpy to do it."""

__author__ = "Sean Donnellan"
__copyright__ = "Copyright (C) 2021 Sean Donnellan"

import hgt
import numpy


def read_hgt_points(hgt_path):
    """Read a HGT (height) file  as a numpy array of the form (hgt_size, 3).

    The resulting array is of the form (longitude, latitude, height) where
    heights are in meters referenced to the WGS84/EGM96 geoid.

    HGT is a data file of the Shuttle Radar Topography Mission (SRTM) as points
    (x, y, z).

    For more information about HGT itself, see hgt.read_hgt().
    """
    size = hgt.size_hgt(hgt_path)
    latitude, longitude = hgt.location_hgt(hgt_path)

    xx, yy = numpy.meshgrid(
        numpy.linspace(longitude, longitude + 1, size),
        numpy.linspace(latitude, latitude + 1, size),
        )

    positions = numpy.zeros((size * size, 3), dtype=numpy.float)
    positions[:,0] = xx.ravel()
    positions[:,1] = yy.ravel()

    # The following gives:
    #  12 13 14 15
    #   8  9 10 11
    #   4  5  6  7
    #   0  1  2  3
    # What I need is:
    #   0  1  2  3
    #   4  5  6  7
    #   8  9 10 11
    #  12 13 14 15
    # This is where numpy.flip() comes in.

    heights = numpy.array(hgt.read_hgt(hgt_path)).reshape(size, -1)
    positions[:,2] = numpy.flip(heights, 0).ravel()
    return positions
