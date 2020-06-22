"""Generates the vertices and facets for Platonic solid.

A Platonic solid is a regular, convex polyhedron in three-dimensional space.

Their faces meet the following properties:
- All angles equal and all sides equal
- polygonal faces with the same number of faces meeting at each vertex
- identical in shape and size

Platonic solid are:
- Tetrahedron (four faces)
- Cube (six faces)
- Octahedron (eight faces)
- Dodecahedron (twelve faces)
- Icosahedron (twenty faces)
"""

# Intresting ideas for this is to produce the net.
# https://en.wikipedia.org/wiki/Net_(polyhedron)

import math


def _edge_length(vertices, reference_face):

    def distance_between_two_points(point_a, point_b):
        x0, y0, z0 = point_a
        x1, y1, z1 = point_b

        return math.sqrt(
            (x0 - x1) ** 2 +
            (y0 - y1) ** 2 +
            (z0 - z1) ** 2
        )

    a, b, c = reference_face
    point_a = vertices[a]
    point_b = vertices[b]
    point_c = vertices[c]

    # ALl sides should be equal length
    edge_ab = distance_between_two_points(point_a, point_b)
    edge_ac = distance_between_two_points(point_a, point_c)
    edge_bc = distance_between_two_points(point_b, point_c)

    # For Platonic solids all edges are the same length.
    #
    # This won't work for the cubes as the face have been split into
    # a triangles and the edge of the hypotenuse will be longer.
    assert edge_ab == edge_ac
    assert edge_ab == edge_bc
    return edge_ab


def tetrahedron(edge_length=2 * math.sqrt(2)):
    """A tetrahedron has four triangular faces and six edges.

    This solid is also known as a triangular pyramid.
    """

    # TODO: Support edge_length

    # The following will have an edge length of 2 * sqrt(2).
    vertices = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]

    facets = [
        (0, 1, 2),
        (3, 1, 2),
        (0, 3, 2),
        (0, 1, 3)  # The base
    ]

    print(_edge_length(vertices, facets[0]))
    return vertices, facets


def cube(edge_length):
    """A cube has six square faces and twelve edges.

    The function will return triangular facets rather than quadrilateral facets, so
    each square face will become two triangles, giving twelve facets.

    This solid is also known as:
    - a square parallelepiped
    - an equilateral cuboid
    - a right rhombohedron
    - a regular hexahedron
    """

    half_edge_length = edge_length / 2

    vertices = [
        (half_edge_length, half_edge_length, half_edge_length),
        (half_edge_length, -half_edge_length, half_edge_length),
        (-half_edge_length, -half_edge_length, half_edge_length),
        (-half_edge_length, half_edge_length, half_edge_length),

        (half_edge_length, half_edge_length, -half_edge_length),
        (half_edge_length, -half_edge_length, -half_edge_length),
        (-half_edge_length, -half_edge_length, -half_edge_length),
        (-half_edge_length, half_edge_length, -half_edge_length),
    ]

    # An improvement to the faces would be to have all the triangles that form
    # the sides of the cube, forming two larger triangles instead of
    # parallelograms.
    faces = [
        (0, 1, 2),
        (0, 2, 3),
        (0, 1, 5),
        (0, 5, 4),
        (0, 4, 7),
        (0, 7, 3),
        (3, 2, 6),
        (3, 6, 7),
        (1, 6, 5),
        (1, 6, 2),
        (4, 5, 6),
        (4, 6, 7)
    ]

    return vertices, faces


def octahedron(edge_length=math.sqrt(2)):
    """A octahedron has eight triangular faces and twelve edges.

    The octahedron is the dual polyhedron to the cube.
    """

    vertices = [
        (0, 0, -1),
        (0, 0, 1),
        (0, -1, 0),
        (0, 1, 0),
        (1, 0, 0),
        (-1, 0, 0),
    ]

    faces = [
        (0, 2, 5),
        (0, 5, 3),
        (0, 3, 4),
        (0, 4, 2),
        (1, 5, 2),
        (1, 2, 4),
        (1, 4, 3),
        (1, 3, 5),
    ]

    return vertices, faces


def dodecahedron(edge_length):
    """A dodecahedron has twelve triangular faces."""
    raise NotImplementedError()


def icosahedron(edge_length=2):
    """A icosahedron has twenty triangular faces and thirty edges.

    This is the convex regular icosahedron.
    """

    # TODO: Support edge_length

    # https://en.wikipedia.org/wiki/Regular_icosahedron
    # Going forward it would be nice to implement the stellations of the icosahedron.

    # Coordinates are (0, +/-1, +-golden_ratio)
    golden_ratio = (1 + math.sqrt(5)) / 2
    vertices = [
        (-1, golden_ratio, 0),
        (1, golden_ratio, 0),
        (-1, -golden_ratio, 0),
        (1, -golden_ratio, 0),
        (0, -1, golden_ratio),
        (0,  1, golden_ratio),
        (0, -1, -golden_ratio),
        (0,  1, -golden_ratio),
        (golden_ratio, 0, -1),
        (golden_ratio, 0,  1),
        (-golden_ratio, 0, -1),
        (-golden_ratio, 0, 1),
    ]

    facets = [
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (5, 4, 9),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1),
    ]

    return vertices, facets
