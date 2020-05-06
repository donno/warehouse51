#!/usr/bin/env python
"""Parses the Commander Keen level file format.

Special thanks to Andrew Durdin for reverse engineering the format.
And http://www.shikadi.net/moddingwiki/GameMaps_Format

Additional information http://files.keenmodding.org/mobydoc.txt

This is very much a work in-progress.

The things that would need to be done to get this to work is:
- Decompressing the LZEXE (I've skipped this by doing it externally).
- Decoding the tile set (I've skipped this by extract it with another tool)
"""

from PIL import Image

# The common functionality needs to go in its own module.
from wolf3d_map import map_headers, level_header, read_plane

class TileSet:
    """
    The tiles are stored in Egagraph.ck4 but I haven't written an extractor
    for that yet. So the tile set can't be extracted from the original files
    yet.

    The EGAHEAD which is the header information from the graphics file is
    stored inside the executable like the MAPHEAD is.
    According to http://www.shikadi.net/moddingwiki/TED5, the EGAHEAD file
    can be found within the executable by looking for the file size of
    the EGAGRAPH within the executable.
    """
    def __init__(self, filename):
        self.image = Image.open(filename)
        self.tile_width = 16
        self.tile_height = 16
        self.tiles_across = self.image.size[0] / self.tile_width

    def __getitem__(self, index):
        """Return a tile."""
        tile_x = index % self.tiles_across
        tile_y = index // self.tiles_across

        image_x = self.tile_width * tile_x
        image_y = self.tile_height * tile_y

        box = (
            image_x, image_y,
            image_x + self.tile_width, image_y + self.tile_height,
            )

        return self.image.crop(box)


def write_level_to_image(level, plane, filename):
    """Write the given level and plane to a image file.

    In practice the planes should be merged to generate a map of the level.
    """

    tile_set = TileSet("keen4_tileset.png")

    level_image = Image.new('RGB', (level.width * tile_set.tile_width,
                                    level.height * tile_set.tile_height))

    def row_column():
        for row in range(level.height):
            for column in range(level.width):
                yield row, column

    for (row, column), tile_index in zip(row_column(), plane):
        tile = tile_set[tile_index]
        level_image.paste(tile, (column * tile_set.tile_width,
                                    row * tile_set.tile_height))

    level_image.save(filename, 'PNG')


def read_keen_map_header(executable_path):
    """Read the MAPHEAD for Commader Keen from the executable itself.

    Unlike for Wolfenstein 3-D the MAPHEAD is stored within the executable.

    On top of that the executable is compressed with LZEXE v0.91. At
    this time, this function required the executable be decompressed first.

    I found success using unlzexe (http://www.shikadi.net/keenwiki/UNLZEXE).
    """
    offsets = {
        #4: 0x24830, # According to the shikadi keenwiki.
        4: 0x27630, # Based on finding it from unlzexe.
        5: 0x25990, # According to the shikadi keenwiki.
        6: 0x25080, # According to the shikadi keenwiki.
    }

    with open(executable_path, 'rb') as exe:
        magic = exe.read(2)
        assert magic == b'MZ', "Should be a executable."

        # Jump to the relocation table offset.
        # http://formats.kaitai.io/dos_mz/dos_mz.svg
        exe.seek(24)
        relocation_table_offset = int.from_bytes(
            exe.read(2), byteorder='little', signed=False)

        assert relocation_table_offset == 0x1C

        exe.seek(0x1C)
        compressed_bytes = exe.read(4)
        assert compressed_bytes != b'LZ09', "Didn't expect LZEXE v0.90."

        if compressed_bytes == b'LZ91': # LZEXE v0.91
            raise ValueError('The executable is compressed.')

        # Jump to the compressed header
        exe.seek(0x27630)
        return map_headers(exe)


def keen():
    """Open the Commander Keen map files.

    For this to work first the executable needs to be unpacked with UNLZEXE.
    http://www.shikadi.net/keenwiki/UNLZEXE
    It might be possible to re-implement that tool using the Python package:
        lzw3 - https://pypi.org/project/lzw3/

    The MAPHEAD for Commander Keen is stored in the executable itself.
    """

    uses_rlew_compression, level_offsets = read_keen_map_header(
        'Keen4e.exeExpanded')

    with open('Gamemaps.ck4', 'rb') as f:
        magic = f.read(8)
        assert magic == b'TED5v1.0'

        for level_number, level_offset in enumerate(level_offsets):
            if level_offset == 0:
                break

            level = level_header(f, level_offset)

            # The tile set for the image generation is only for
            # plane 0.
            plane_index = 0
            offset_to_plane, length_of_plane = level.plane(plane_index)
            plane = read_plane(f, offset_to_plane, length_of_plane,
                                uses_rlew_compression)

            write_level_to_image(
                level,
                plane,
                filename=f"level_{level_number}_{level.name}_{plane_index}.png")

if __name__ == '__main__':
    keen()