"""Generate a Sierpinski Triangle which is a fractal attractive fixed set.

https://en.wikipedia.org/wiki/Sierpi%C5%84ski_triangle
"""

import math

import solids.platonic


def _midpoint(point_a, point_b):
    point_a_x, point_a_y, point_a_z = point_a
    point_b_x, point_b_y, point_b_z = point_b

    return (
        (point_a_x + point_b_x) / 2.0,
        (point_a_y + point_b_y) / 2.0,
        (point_a_z + point_b_z) / 2.0,
    )


def _divide(triangle, points):
    """Divide a equilateral triangle into three more equilateral triangle."""
    a, b, c = triangle

    # Insert points midway along each side of the triangle.
    # Form 3 new triangles.
    new_vertices = [
        _midpoint(points[a], points[b]),
        _midpoint(points[b], points[c]),
        _midpoint(points[c], points[a]),
    ]

    new_vertices_indices = [
        len(points),
        len(points) + 1,
        len(points) + 2,
    ]

    new_triangles = [
        (a, new_vertices_indices[0], new_vertices_indices[2]),
        (b, new_vertices_indices[1], new_vertices_indices[0]),
        (c, new_vertices_indices[2], new_vertices_indices[1]),
    ]

    return new_vertices, new_triangles


def triangle_edges(length=2.0, divisions=4)):
    """Generates the points and edges to form a Sierpinski triangle."""

    def _edges_from_triangle(triangle):
        a, b, c = triangle
        return [(a, b), (b, c), (c, a)]

    vertices, facets = triangle_facets(length, divisions)
    edges = []
    for facet in facets:
        edges.extend(_edges_from_triangle(facet))
    return vertices, edges


def triangle_facets(length=2.0, divisions=4):
    """Generates the points and facets to form a Sierpinski triangle."""

    # Starting with a equilateral triangle.
    vertices = [
        (0, (math.sqrt(3) / 3.0) * length, 0.0),
        (-length / 2, -(math.sqrt(3) / 6.0) * length, 0.0),
        (length / 2, -(math.sqrt(3) / 6.0) * length, 0.0),
    ]

    # The facets should not be accumulated for all of them as the first
    # triangle will Z-fight with remaining triangles. The overall style is to
    # have 'holes' where there are triangles that aren't filled.

    facets = [(0, 1, 2)]
    new_triangles = facets

    for _ in range(divisions):
        facets = []
        for new_triangle in new_triangles:
            next_vertices, next_triangles = _divide(new_triangle, vertices)
            vertices.extend(next_vertices)
            facets.extend(next_triangles)

        new_triangles = facets

    return vertices, facets
