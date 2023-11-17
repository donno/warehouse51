"""Read GOCAD Tsurf files.

tsurf is a triangulation (formed from triangles) has extension .ts (not video).
tsolid is formed from tetras and has extension .so (not Shared Object)
pline is a polygonal line and has extension .pl (not Perl).

Documentation:
https://web.archive.org/web/20080411233135/http://www.earthdecision.com/products/developmentkit_ascii.html
"""

import bisect
import enum
import itertools
import numpy


class State(enum.IntEnum):
    WAITING_FOR_HEADER = 0
    WITHIN_HEADER = 1
    WAITING_FOR_BODY = 2
    WITHIN_BODY = 3
    WAITING_FOR_END = 4


def parsed_lines(reader):
    for line in reader:
        if line.startswith("#"):  # Comment
            continue

        parts = line.strip().split()
        keyword = parts[0]
        yield keyword, parts[1:]


def read_group(reader):
    values = {}

    for line in reader:
        if line.startswith("#"):  # Comment
            continue
        if line.startswith("}"):  # End of header.
            break

        if ":" in line:
            key, _, value = line.partition(":")
            values[key] = value
        elif line.endswith("{\n"):
            raise ValueError("Unexpected subgroup with in group")
        elif all(c.isdigit() or c in (" ", ".", "\n") for c in line):
            # Only numbers.
            # In the case observed this was a continuation of previous
            # line
            values[key] += line
        else:
            raise ValueError(f"Unexpected line: {line}")

    return values


def read_header(reader):
    line = reader.readline()
    if not line.startswith("HEADER {"):
        raise ValueError(f"Expected HEADER found {line}")

    header = {}

    for line in reader:
        if line.startswith("#"):  # Comment
            continue
        if line.startswith("}"):  # End of header.
            break

        if ":" in line:
            key, _, value = line.partition(":")
            header[key] = value[:-1]
        elif line.endswith("{\n"):
            parts = line.split(" ")
            # children = read_group(reader)
            # print(parts[0], children)
        else:
            # raise ValueError(f"Unexpected line: {line}")
            # Ignore everything else.
            pass

    # Apparently the header suppose to end when it hits PROPERTY_CLASS_HEADER
    # Not the }

    # PROPERTY_CLASS_HEADER
    return header


def read_property_class_header(reader):
    """Skips over the property class header"""
    for line in reader:
        if line.startswith("#"):  # Comment
            continue
        if line.startswith("}"):  # End of header.
            break


def read_atom_region_indicators(reader):
    for keyword, arguments in parsed_lines(reader):
        if keyword == 'ARI':
            # This could collect all the values and then return when done.
            pass  # Ignore this for now.
        elif keyword == 'END_ATOM_REGION_INDICATORS':
            break
        else:
            raise NotImplementedError(
                f"Unexpected kind {keyword} with the atom region indicators")


def read_property(reader, property_type):
    values = []

    for keyword, arguments in parsed_lines(reader):
        if keyword == f"{property_type}P":
            if len(arguments) > 1:
                raise NotImplementedError(
                    "Dealing with multi-value properties")
            values.append(int(arguments[0]))
        elif keyword == f'END_PROPERTY_{property_type}':
            return values
        else:
            raise NotImplementedError(
                f"Unexpected kind {keyword} with the atom region indicators")


def read_nodes(reader):
    nodes = []
    properties = {}

    for keyword, parts in parsed_lines(reader):
        if keyword in ("SEG", "TRGL"):
            # End of nodes start of elements.
            return nodes, keyword + ' ' + ' '.join(parts)
        if keyword == "PVRTX":
            node_id = int(parts[0])
            x, y, z = parts[1:4]
            nodes.append((node_id, x, y, z))

            # Ignore the remaining properties of a node for now.
            #
            # They are from the PROPERTIES line.
            # PROPERTIES U V Dip_Angle FaultStrike
        elif keyword == "VRTX":
            node_id = int(parts[0])
            x, y, z = parts[1:4]
            nodes.append((node_id, x, y, z))
        elif keyword in ("PATOM", "ATOM"):
            # Unsure what a PATOM is, maybe POINT or PROPERTY ATOM
            pass
        elif keyword == "BEGIN_ATOM_REGION_INDICATORS":
            read_atom_region_indicators(reader)
        elif keyword == 'PROPERTY_CN':
            # Start of a property and will end with END_PROPERTY_CN.
            properties[parts[0]] = read_property(reader, 'CN')
        else:
            # VRTX, ATOM and PVRTX are main cases.
            raise NotImplementedError(f"Unexpected kind {keyword}")

    return nodes, None


def read_elements(reader, line):
    triangles = []

    if line and line.startswith("TRGL"):
        parts = line.split()

        # Doesn't handle any extra properties
        # as per TRGL_PROPERTIES at this stage.
        a, b, c = parts[1:4]
        triangles.append((int(a), int(b), int(c)))

    for keyword, parts in parsed_lines(reader):
        if keyword == "TRGL":
            # Doesn't handle any extra properties
            # as per TRGL_PROPERTIES at this stage.
            a, b, c = parts[0:3]
            triangles.append((int(a), int(b), int(c)))
        else:
            return triangles, keyword + ' ' + ' '.join(parts)

    return triangles, None


def read_faces(reader):
    nodes, line = read_nodes(reader)
    elements, line = read_elements(reader, line)

    groups = [(nodes, elements)]

    # READ Something. else.
    while line.startswith(("TFACE", "3DFace")):
        nodes, line = read_nodes(reader)
        elements, line = read_elements(reader, line)
        groups.append((nodes, elements))

    return groups


def read_coordinate_system(reader):
    """Skips over the coordinate system."""

    # At some point this should be read properly./
    for line in reader:
        if line.startswith("#"):  # Comment
            continue
        if line.startswith("END_ORIGINAL_COORDINATE_SYSTEM"):
            break


def read(path):
    # Header
    # Body
    # End

    groups = []

    with open(path, "r") as reader:
        line = reader.readline()

        if not line.startswith("GOCAD"):
            raise ValueError("Expected a GOCAD ASCII file")
        _, type_name, version_number = line.strip().split(" ")

        # This reader could be extended for the other GOCAD ASCII Files.
        if type_name != 'TSurf':
            raise ValueError("Expected a TSurf (Surface) file.")

        if type_name == 'TSurf' and version_number != '1':
            raise ValueError(f"Expected a version 1 file not {version_number}")

        header = read_header(reader)
        print(header)

        # line = reader.readline()
        for line in reader:
            if line.startswith(("TFACE", "3DFace")):
                groups = read_faces(reader)
            elif line.startswith("GOCAD_ORIGINAL_COORDINATE_SYSTEM"):
                read_coordinate_system(reader)
            elif line.startswith("PROPERTY_CLASS_HEADER"):
                read_property_class_header(reader)
            elif line.startswith(("GEOLOGICAL_FEATURE", "GEOLOGICAL_TYPE")):
                pass
            elif line.startswith(("BSTONE", "BORDER")):
                pass  # Borders not implemented.

    if not groups:
        raise ValueError("Found no facets/points")

    point_count = sum(len(nodes) for nodes, _ in groups)
    # vertices = numpy.zeros((point_count, 3))

    iterable = (
        node[1:4]
        for node in itertools.chain.from_iterable(nodes for nodes, _ in groups)
    )
    points = numpy.fromiter(
        iterable, dtype=numpy.dtype((float, 3)), count=point_count)
    vertex_id_to_index = [
        node[0]
        for node in itertools.chain.from_iterable(nodes for nodes, _ in groups)
    ]

    def map_id_to_index(element):
        a, b, c = element

        # This assumes that the index will be found and thus the data is
        # well-formed.
        return (
            bisect.bisect_left(vertex_id_to_index, a),
            bisect.bisect_left(vertex_id_to_index, b),
            bisect.bisect_left(vertex_id_to_index, c),
        )

    facet_iterable = (
        map_id_to_index(element)
        for element in itertools.chain.from_iterable(
            elements for _, elements, in groups
        )
    )
    facets = numpy.fromiter(facet_iterable, dtype=numpy.dtype((int, 3)))
    return points, facets


if __name__ == "__main__":
    # Sample datafile from Los Alamos Grid Toolbox (LaGriT).
    #read("input_3tri_all_props.ts")

    import os
    import sys
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <folder-with-ts_files>")
        sys.exit(1)

    for root, dirname, files in os.walk(sys.argv[1]):
        for file in files:
            if file.endswith('.ts'):
                try:
                    read(os.path.join(root, file))
                except:
                    print(os.path.join(root, file))
                    raise
