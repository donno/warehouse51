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

    new_edges = [
        # Triangle 1
        (a, new_vertices_indices[0]),
        (new_vertices_indices[0], new_vertices_indices[2]),
        (new_vertices_indices[2], a),

        # Triangle 2
        (b, new_vertices_indices[1]),
        (new_vertices_indices[1], new_vertices_indices[0]),
        (new_vertices_indices[0], b),

        # Triangle 3
        (c, new_vertices_indices[2]),
        (new_vertices_indices[2], new_vertices_indices[1]),
        (new_vertices_indices[1], c),
    ]

    new_triangles = [
        (a, new_vertices_indices[0], new_vertices_indices[2]),
        (b, new_vertices_indices[1], new_vertices_indices[0]),
        (c, new_vertices_indices[2], new_vertices_indices[1]),
    ]

    return new_vertices, new_edges, new_triangles


def triangle_edges(length=2.0):
    """Generates the points and edges to form a Sierpinski triangle."""

    # Starting with a equilateral triangle.
    vertices = [
        (0, (math.sqrt(3) / 3.0) * length, 0.0),
        (-length / 2, -(math.sqrt(3) / 6.0) * length, 0.0),
        (length / 2, -(math.sqrt(3) / 6.0) * length, 0.0),
    ]
    edges = [(0, 1), (1, 2), (2, 0)]

    triangle = (0, 1, 2)
    new_vertices, new_edges, new_triangles = _divide(triangle, vertices)
    vertices.extend(new_vertices)
    edges.extend(new_edges)

    # For more dividing use new_triangles
    for new_triangle in new_triangles:
        new_vertices, new_edges, _ = _divide(new_triangle, vertices)
        vertices.extend(new_vertices)
        edges.extend(new_edges)

    return vertices, edges


def triangle_facets(length=2.0):
    """Generates the points and facets to form a Sierpinski triangle."""

    # Starting with a equilateral triangle.
    vertices = [
        (0, (math.sqrt(3) / 3.0) * length, 0.0),
        (-length / 2, -(math.sqrt(3) / 6.0) * length, 0.0),
        (length / 2, -(math.sqrt(3) / 6.0) * length, 0.0),
    ]

    triangle = (0, 1, 2)
    new_vertices, _, new_triangles = _divide(triangle, vertices)
    vertices.extend(new_vertices)

    # The facets should not be accumulated for all of them as the first
    # triangle will Z-fight with remaining triangles. The overall style is to
    # have 'holes' where there are triangles that aren't filled.
    facets = []
    for new_triangle in new_triangles:
        new_vertices, _, triangles = _divide(new_triangle, vertices)
        vertices.extend(new_vertices)
        facets.extend(triangles)

    return vertices, facets
