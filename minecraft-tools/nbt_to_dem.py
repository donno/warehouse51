"""Produce a digital elevation model (DEM) from a Minecraft world (NBT format).

The idea is to produce two different versions DTM and DSM.

Outside the scope at this time is producing an production an orthophotograph,
i.e. an aerial image of the world looking down.

Glossary:
- DEM - Digital Elevation Model
- DSM - Digital Surface Model
  Includes all features on the Earth's surface, such as buildings and trees.
- DTM - Digital Terrain Model
  Represents only the bare-earth surface, removing all above-ground features.
- NBT- Named Binary Tag
  Tree data structure used by Minecraft in many save files to store arbitrary
  data.

Minecraft is a registered trademark owned by Microsoft Corporation.
"""

# /// script
# dependencies = [
#   "nbt",
#   "numpy",
# ]
# ///

# Standard library imports
import argparse
import pathlib

# Third party imports
from nbt.world import WorldFolder
from nbt.chunk import Chunk

# If they believe np would be a better name they should have named it np
# instead of calling it numpy.
import numpy  # noqa: ICN001

NON_SOLID_BLOCK_TYPES = [0, 8, 9, 10, 11, 38, 37, 32, 31]
"""The (type) index of a non-solid block.

For example, 0 is air, 8 and 9 are water, 10 and 11 are lava.
"""

ABOVE_GROUND_BLOCK_NAMES = [
    "minecraft:grass",
    # Grass block is allowed as it is more like a dirt block with grass on it.
]
"""The name of blocks of block types that are above ground.

These are blocks that are suitable for a surface model but not terrain model.
These blocks are also suitable for the orthophotograph.
"""

# The above approach is tackle this from the above layer and safe what is a
# valid terrain block which would be grass, dirt, stone and the ores.


def determine_top_most_block_for_chunk(
    chunk: Chunk,
    *,
    exclude_above_ground_types: bool,
) -> tuple[numpy.array, numpy.array]:
    """Determine the top most block in the given chunk.

    If ignore exclude_above_ground_types is True then it ignores blocks such as
    leaves and trees, thereby making it suitable to produce a digital terrain
    model.

    Returns the 16 x 16 array of depths and 16 x 16 array of block types.

    TODO: Consider if it would be more useful to return the block names instead
    indices.
    """
    section_indices = sorted(chunk.sections.keys(), reverse=True)

    empty_block = 2

    # Keep track of the last seen block
    depths = numpy.zeros((16, 16))
    depths.fill(-1)
    blocks = numpy.zeros((16, 16))
    blocks.fill(empty_block)

    for section_index in section_indices:
        section = chunk.sections[section_index]
        world_y = 16 * section_index
        for y in range(15, -1, -1):
            for z in range(16):
                for x in range(16):
                    if blocks[x][z] != empty_block:
                        # Already found the target for this column.
                        continue

                    offset = y * 256 + z * 16 + x
                    block_type = section.indexes[offset]

                    # If the block is not solid then ignore it.
                    if block_type in NON_SOLID_BLOCK_TYPES:
                        continue

                    if exclude_above_ground_types:
                        block_name = section.names[block_type]
                        if block_name in ABOVE_GROUND_BLOCK_NAMES:
                            continue

                    blocks[x][z] = block_type
                    depths[x][z] = world_y - y
    return depths, blocks


def determine_top_most_block(
    world: WorldFolder,
    *,
    exclude_above_ground_types: bool,
) -> None:
    """Determine the top most block.

    By default this ignores air.

    If ignore exclude_above_ground_types is True then it ignores blocks such as
    leaves and trees, thereby making it suitable to produce a digital terrain
    model.
    """
    for chunk in world.iter_chunks():
        depths, blocks = determine_top_most_block_for_chunk(
            chunk,
            exclude_above_ground_types=exclude_above_ground_types,
        )

        chunk_x, chunk_z = chunk.get_coords()
        world_x = chunk_x * 16
        world_z = chunk_z * 16

        print(f"World: {world_x},{world_z}")
        print(blocks, "@", depths, sep="\n")

    # The easy/quick way to write this out to a TIFF file would be to create
    # 16 by 16 tiles in the resulting TIFF file and thus write each tile out.

    print("TODO: Creating the TIFF file is not yet implemented.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Minecraft world to a digital elevation model.\n",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dtm",
        action="store_true",
        help="Produce a digital terrain model - bare earth removing all "
        "above-ground features (blocks in Minecraft terms).",
    )
    group.add_argument(
        "--dsm",
        action="store_true",
        help="Produce a digital surface model - include tree tops",
    )
    parser.add_argument(
        "world_directory",
        nargs="?",
        help="folder containing the Minecraft world",
        default=pathlib.Path.home() / "AppData/Roaming/.minecraft/saves" / "NewWorld",
        type=pathlib.Path,
    )

    parser.add_argument(
        "--output",
        nargs="?",
        help="the path to output the TIFF file.",
        default=pathlib.Path.cwd() / "mc_dem.tif",
        type=pathlib.Path,
    )

    arguments = parser.parse_args()
    world = WorldFolder(arguments.world_directory)
    determine_top_most_block(world, exclude_above_ground_types=True)
