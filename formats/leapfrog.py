"""A module for working with Leapfrog files - at this time only meshes.

The data used to develop and test this reader was from the New South Wales
government of Australia.

3D geological mapping data -> Package Cobar geological and fault model package.
Found at: https://www.resourcesregulator.nsw.gov.au/meg.site/geoscience/products-and-data/3d-geological-mapping-data
"""

import numpy
import os
import struct
import types


def read_leapfrog_mesh(path):
    """Read a Leapfrog mesh (.msh) file.

    Return
    ------
    tuple
        The name of the file sans extension, the points and facets.
    """
    expected_header = b"%ARANZ-1.0\n\n"
    expected_binary_header = b"[binary]"

    index = []

    def _decode_index_item(item):
        components = item.decode("utf-8").split(" ")
        if components[-1].endswith(";"):
            components[-1] = components[-1][:-1]

        if len(components) != 4:
            raise ValueError("Expected index to only contain 4 values.")

        return types.SimpleNamespace(
            field_name=components[0],
            field_type=components[1],
            type_per_item=int(components[2]),
            count=int(components[3]),
        )

    def field_to_struct_format(field):
        """Convert the field from the index to the format for struct module."""
        field_type_to_format_type = {
            "Integer": "i",
            "Float": "f",
            "Single": "f",
            "Double": "d",
        }
        format_type = field_type_to_format_type[field.field_type]
        return f"{field.count * field.type_per_item}{format_type}"


    with open(path, "rb") as reader:
        header = reader.read(len(expected_header))
        if header != expected_header:
            raise ValueError("File is not a supported a Leapfrog mesh file.")

        line = reader.readline()
        if line == b"[index]\n":
            for line in reader:
                if line == b"\n":
                    break  # End of the index.
                index.append(_decode_index_item(line[:-1]))
        else:
            raise ValueError("Expected index but didn't find it.")

        print(index)
        struct_format = ''.join(map(field_to_struct_format, index))

        binary_header = reader.read(len(expected_binary_header))
        if binary_header == b"[binary]":
            separator_size = struct.calcsize("3i")
            separator = struct.unpack_from("3i", reader.read(separator_size))
            assert separator == (15732735, 1115938331, 1072939210)

            binary = reader.read()  # Read all of it for now.

            data = struct.unpack_from(struct_format, binary)

            # Split the data
            #
            # I haven't worked on making this part general yet so for now
            # it will simply assume a fixed order.
            assert index[0].field_name == "Tri"
            assert index[1].field_name == "Location"

            facet_end = index[0].count * index[0].type_per_item
            facets = data[:facet_end]
            facets = numpy.array(facets).reshape((-1, index[0].type_per_item))

            points = data[
                facet_end : facet_end + index[1].count * index[1].type_per_item
            ]
            points = numpy.array(points).reshape((-1, index[1].type_per_item))
            return os.path.splitext(os.path.basename(path))[0], facets, points
        else:
            raise ValueError("Expected binary but didn't find it.")
