"""Turn a grid of heights into a triangulation.

The common alternative representation which stores the data as triangles instead
of a a grid of heights (i.e dense raster model as common in a digital
elevation model) are a Triangulated Irregular Network or TIN.

In computational geometry they are known as polyhedral terrain.


Approaches:
- Create two triangle for each quad formed by the neighbouring 4 points within
  the grid. This is what the triangles() function does.
- New approach (not implemented).
    1. Selecting Sampling Points - Determine which points to use, the better
      the sampling the better the resulting model, with several researched
      options:
      a. Fowler and Little’s algorithm (1979)
      b. The Very Important Points algorithm (Chen & Guevara, 1987).
         Chen, Zi-Tan, and J. Armando Guevara. "Systematic selection of very
         important points (VIP) from digital terrain model for constructing
         triangular irregular networks." Auto-Carto. Vol. 8. 1987.
    2. Triangulation
       a. Delaunay triangulation (Delaunay, 1934).
       b. Divide-and-Conquer algorithm (Lewis & Robinson, 1978)
       c. Convex Hull Insertion (Tsai & Vonderohe, 1991).
"""

import io
import itertools
import math
import typing

import hgt


def heights_to_points(origin, heights):
    """Convert the heights to points (x, y, z).

    X and y are in degrees and z is in metres.

    Parameters
    ----------
    origin
        The origin (x, y) of the heights, which is the lower-left corner.
    """

    origin_x, origin_y = origin
    size = int(math.sqrt(len(heights)))

    # Heights are in row-major so the first two heights only different in
    # the x direction. However, first height is the top-left corner.
    for (x, y), z in zip(itertools.product(range(size -1, -1, -1),
                                           range(size -1, -1, -1)),
                         heights):
        yield origin_x + x / size, origin_y + y / size, z


def triangles(heights):
    """Generate triangles that connect the points.

    This is a very naive approach and will result in almost 26 million
    triangles.
    """
    size = int(math.sqrt(len(heights)))

    #  The layout of the quad is:
    #  TL---TR
    #   |   |
    #   |   |
    #  BL---BR
    #
    #  The resulting triangles will be:
    #
    # TL---TR       TL---TR
    #  |  /|   or    |\  |
    #  | / |         |  \|
    # BL---BR       BL---BR
    #
    # 0---1        0---1
    # |  /|   or   |\  |
    # | / |        |  \|
    # 3---2        3---2

    # This needs to stop on the last column and before the last row.
    for column, row in itertools.product(range(size - 1), range(size - 1)):
        top_left_point = column + row * size
        top_right_point = top_left_point + 1
        bottom_left_point = top_left_point + size
        bottom_right_point = top_right_point + size

        if (heights[top_left_point] - heights[bottom_right_point] <
            heights[top_right_point] - heights[bottom_left_point]):
            yield top_left_point, bottom_right_point, bottom_left_point
            yield top_right_point, bottom_right_point, top_left_point
        else:
            # NE-SW edge is shortest
            yield (top_right_point, bottom_right_point, bottom_left_point)
            yield (top_left_point, top_right_point, bottom_left_point)


def hgt_to_ply(hgt_path: str, output: typing.IO[str] ):
    """Convert a HGT file into a PLY (Polygon File Format).

    The resulting files will have be difficult to view in various software.
    """
    # Heights are in meters referenced to the WGS84/EGM96 geoid.
    #Data voids are assigned the value -32768
    # TODO: Handle NO_DATA_VALUE , where by the points need to be omitted
    # and thus the triangles too.

    # This is the lower left corner.
    origin = hgt.location_hgt(hgt_path)
    heights = hgt.read_hgt(hgt_path)

    vertex_count = len(heights)
    face_count = len(heights) * 2

    # Output header.
    output.write('ply\n')
    output.write('format ascii 1.0\n'),
    output.write(f'element vertex {vertex_count}\n')
    output.write('property float x\n')
    output.write('property float y\n')
    output.write('property float z\n')

    output.write(f'element face {face_count}\n')
    output.write('property list uchar int vertex_index\n')
    output.write('end_header\n')

    for x, y, z in heights_to_points(origin, heights):
        output.write(f"{x:.9f} {y:.9} {z}\n")

    for triangle in triangles(heights):
        a, b, c = triangle
        output.write(f"3 {a} {b} {c}\n")


if __name__ == "__main__":
    # output = io.StringIO()
    with open('N03W074.ply', 'w', encoding='ascii') as output:
        hgt_to_ply('N03W074.hgt', output)
    # print(output.getvalue())
