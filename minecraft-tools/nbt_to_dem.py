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
#   "tifffile",
# ]
# ///

# Standard library imports
import argparse
import itertools
import pathlib

# Third party imports
from nbt.world import WorldFolder, InconceivedChunk
from nbt.chunk import Chunk

# If they believe np would be a better name they should have named it np
# instead of calling it numpy.
import numpy  # noqa: ICN001
import tifffile

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


def _debug(
    world: WorldFolder,
    *,
    exclude_above_ground_types: bool,
) -> None:
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


def write_digital_elevation_model(
    world: WorldFolder,
    destination: pathlib.Path,
    *,
    exclude_above_ground_types: bool,
) -> None:
    """Write a digital elevation mode representing world to destination.

    The destination will be a TIFF (Tagged Image File Format) file.

    If ignore exclude_above_ground_types is True then it ignores blocks such as
    leaves and trees, thereby making it suitable to produce a digital terrain
    model rather than digital surface model.
    """
    model_type = "terrain" if exclude_above_ground_types else "surface"
    metadata = {
        "Description": f"A digital {model_type} model (digital elevation "
        "model) created from a Minecraft world.",
    }

    def chunks(world: WorldFolder) -> itertools.product[tuple[int, int]]:
        bounding_box = world.get_boundingbox()
        xs = range(bounding_box.minx, bounding_box.maxx)
        zs = range(bounding_box.minz, bounding_box.maxz)
        return itertools.product(xs, zs)

    # # The easy/quick way to write this out to a TIFF file would be to create
    # # 16 by 16 tiles in the resulting TIFF file and thus write each tile out.

    def tiles(world: WorldFolder):
        """Generate the data for the tiles."""
        for chunk_x, chunk_z in chunks(world):
            try:
                chunk = world.get_chunk(chunk_x, chunk_z)
                depths, _ = determine_top_most_block_for_chunk(
                    chunk,
                    exclude_above_ground_types=exclude_above_ground_types,
                )
                yield depths
            except InconceivedChunk:
                # The chunk has not been generated so treat it as empty / no
                # data
                #
                # TODO: Confirm how tifffile handles this case.
                # It doesn't seem to support yielding None here.
                yield numpy.zeros((16, 16))

    bounding_box = world.get_boundingbox()
    shape = (
        16 * (bounding_box.maxx - bounding_box.minx),
        16 * (bounding_box.maxz - bounding_box.minz),
        1,  # For RGB this would be a 3
    )

    tifffile.imwrite(
        destination,
        tiles(world),
        tile=(16, 16),
        shape=shape,
        dtype=numpy.float64,  # Metres
        bigtiff=True,
        compression="zlib",
        compressionargs={"level": 8},
        metadata=metadata,
    )


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
    write_digital_elevation_model(
        world,
        arguments.output,
        exclude_above_ground_types=arguments.dtm,
    )
