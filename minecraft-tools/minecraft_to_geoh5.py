"""Import each chunk in a Minecraft world as a block model in a GeoH5 workspace

This uses the nbt package by twoolie from https://github.com/twoolie/NBT for
reading Minecraft world and geoh5py package

TODO:
- Produce a colour map
- Merge chunks together so they are a 5x5 chunks.
- Determine if its possible to set-up filtering / visibility so the air
  blocks aren't visible.
  """

# /// script
# dependencies = [
#   "nbt",
#   "geoh5py",
# ]
# ///


from geoh5py.objects import BlockModel
from geoh5py.workspace import Workspace


from nbt.world import WorldFolder, InconceivedChunk
from nbt.nbt import NBTFile

import numpy

import argparse
import itertools
import os
import pathlib


class UnexpectedEmptyChunk(ValueError):
    def __init__(self):
        super().__init__("Chunk has no section so is empty.")


def level_details(world):
    # See https://minecraft.gamepedia.com/Level_format#level.dat_format
    level_path = os.path.join(world.worldfolder, "level.dat")
    level = NBTFile(filename=level_path)["Data"]

    difficulty_to_name = {
        0: "Peaceful",
        1: "Easy",
        2: "Normal",  # This is the default.
        3: "Hard",
    }

    return {
        "Name": level["LevelName"].value,
        "Difficulty": difficulty_to_name[level["Difficulty"].value],
        "Time": level["Time"].value,
    }


def grouped_chunks(world, size=3):
    """Groups the chunks into the given size in both northing and easting.

    Yields the Group (centre and lower_left), size (in both directions) and
    the list of chunk coordinates (indices).
    """
    bounding_box = world.get_boundingbox()

    # The bounding box does not cover if there is a big row or column of chunks
    # missing that simply haven't been generated yet.
    #
    # It would be handy if the below code that tries to clamp it could check
    # and thus avoid missing chunks if the entire row or column is missing.

    from_centre_to_right = range(0, bounding_box.maxx, size)
    from_left_to_centre = range(0, bounding_box.minx, -size)
    from_centre_to_top = range(0, bounding_box.maxz, size)
    from_bottom_to_centre = range(0, bounding_box.minz, -size)

    class Group:
        """A grouping of chunk.

        Centre is the chunk coordinate of the centre chunk.
        Lower left is the chunk coordinate of the chunk that forms the lower
        left corner of the group.
        """

        def __init__(self, centre, lower_left):
            self.centre = centre
            self.lower_left = lower_left

        @property
        def lower_left_world(self):
            """The lower left coordinate of the group in world space.

            Rather than as the chunk index.
            """
            return (self.lower_left[0] * 16, self.lower_left[1] * 16, 0)

    # While progress wise it would be nicer to start from the centre and work
    # outwards. It is simpler going this way.
    for centre in itertools.product(
        itertools.chain(from_left_to_centre, from_centre_to_right),
        itertools.chain(from_bottom_to_centre, from_centre_to_top),
    ):

        start_x = max(centre[0] - size // 2, bounding_box.minx)
        end_x = min(centre[0] + size // 2 + 1, bounding_box.maxx)

        # This is using NBT's semantics that the height above ground is Y
        # rather than Z.
        start_z = max(centre[1] - size // 2, bounding_box.minz)
        end_z = min(centre[1] + size // 2 + 1, bounding_box.maxz)

        # These will be equal to size unless clamping was applied.
        true_size = (end_x - start_x), (end_z - start_z)

        chunks = itertools.product(range(start_x, end_x), range(start_z, end_z))

        yield Group(centre, (start_x, start_z)), true_size, chunks


def convert_grouped_chunks(world_folder, workspace, group_size=3):
    """Convert group chunks and convert them as a single block model.

    See grouped_chunks for details on group_size.
    """
    world = WorldFolder(world_folder)  # map still only supports McRegion maps
    level = level_details(world)

    def _convert_chunk_to_block_types(chunk_coordinate):
        """Return the block types (indices).

        These indices are section specific."""

        # If this ends up being useful, replace the next function with
        # one that can take the indices (and maybe the block names for this
        # one) and return it.

        try:
            chunk = world.get_chunk(*chunk_coordinate)
        except InconceivedChunk:
            # The chunk has likely not be generated so we will fill it with
            # air for now.
            block_types = numpy.empty((256, 16, 16), dtype=numpy.uint32)
            block_types.fill(0)
            return block_types

        block_types = numpy.empty(256 * 16 * 16, dtype=numpy.uint32)
        for section_index, section in chunk.sections.items():
            section_start = section_index * len(section.indexes)
            section_end = section_start + len(section.indexes)
            block_types[section_start:section_end] = section.indexes

        return block_types.reshape((256, 16, 16))

    def _convert_chunk_to_block_names(chunk_coordinate):
        """Return block name arrays for the chunk."""
        try:
            chunk = world.get_chunk(*chunk_coordinate)
        except InconceivedChunk:
            # The chunk has likely not be generated so we will fill it with
            # air for now.
            block_names = numpy.empty((256, 16, 16), dtype="U4")
            block_names.fill("air")
            return block_names

        # Handle reading the new format known as Anvil, by reading all the
        # indices at once. This also avoids having to go via the names.
        block_names = [""] * 256 * 16 * 16

        def simply_block_name(name):
            """Removes the minecraft: prefix from block names."""
            needle = "minecraft:"
            if name.startswith(needle):
                name = name[len(needle) :]
            return name

        # Sections are essenitally 16 by 16 by 16.
        for section_index, section in chunk.sections.items():
            section_start = section_index * len(section.indexes)
            section_end = section_start + len(section.indexes)
            block_names[section_start:section_end] = [
                simply_block_name(section.names[index]) for index in section.indexes
            ]

        return numpy.array(block_names).reshape((256, 16, 16))

    # The original plan was to read the values out of the chunk straight
    # into the right location in the block model. However the new approach
    # is to simply generate an array for each chunk then combined the
    # chunks together.

    for group, size, chunks in grouped_chunks(world, group_size):
        chunk_x, chunk_z = group.centre

        block_model = BlockModel.create(
            workspace,
            origin=group.lower_left_world,
            u_cell_delimiters=numpy.cumsum(numpy.ones(17 * size[0])),
            v_cell_delimiters=numpy.cumsum(numpy.ones(17 * size[1])),
            z_cell_delimiters=numpy.cumsum(numpy.ones(257)),
            rotation=0.0,
            name=f"Group_{chunk_x},{chunk_z}",
        )

        # All the chunks that are being grouped have been flatend so we
        # need to turn them back into rows, so we can then merge a single
        # row of chunks together than we can merge the rows together to
        # form the final block model.
        by_x = lambda coordinate: coordinate[0]

        # Instead it might be possible to assemble each numpy.array into
        # nested lists and then use numpy.block() rather than stacking
        # along one axis and than another.
        rows = []
        rows_material_index = []
        for _, chunks in itertools.groupby(chunks, key=by_x):
            chunks = list(chunks)
            rows.append(
                numpy.hstack(
                    tuple(
                        _convert_chunk_to_block_names(chunk_coordinate)
                        for chunk_coordinate in chunks
                    )
                )
            )

            rows_material_index.append(
                numpy.hstack(
                    tuple(
                        _convert_chunk_to_block_types(chunk_coordinate)
                        for chunk_coordinate in chunks
                    )
                )
            )

        block_model.add_data(
            {
                "Material Name": {
                    "association": "CELL",
                    "values": numpy.dstack(rows).T.ravel(),
                },
            },
        )
        block_model.add_data(
            {
                "Material Index": {
                    "association": "CELL",
                    "values": numpy.dstack(rows_material_index).T.ravel(),
                },
            },
        )

        block_model.origin = group.lower_left_world
        block_model.update_metadata(level)
        break


def block_names(world_folder):
    """Return a set of all the block names stored in the given world."""
    world = WorldFolder(world_folder)

    used_block_names = set()
    try:
        for chunk in world.iter_chunks():
            for section in chunk.sections.values():
                used_block_names.update(section.names)
    except KeyboardInterrupt:
        # Stop and report current process.
        pass

    return used_block_names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import the chunks of a Minecraft world into a GeoH5 workspace.",
    )
    parser.add_argument(
        "world_directory",
        nargs="?",
        help="folder containing the data",
        default=pathlib.Path.home() / "AppData/Roaming/.minecraft/saves" /
            "NewWorld",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--output",
        help="the path and name of the GeoH5 file to create.",
        default=pathlib.Path("mcworld.geoh5"),
        type=pathlib.Path,
    )
    arguments = parser.parse_args()

    with Workspace.create(arguments.output) as workspace:
        # TODO: Add a colour map of the block names to colours.
        convert_grouped_chunks(arguments.world_directory, workspace, group_size=5)
