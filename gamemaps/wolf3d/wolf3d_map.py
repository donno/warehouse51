#!/usr/bin/env python
"""Parses the Wolfenstein 3-D level file format.

Special thanks to Andrew Durdin for reverse engineering the format.
And http://www.shikadi.net/moddingwiki/GameMaps_Format

Additional information http://files.keenmodding.org/mobydoc.txt

More details are at which cover the VSWAP file.
  https://devinsmith.net/backups/bruce/wolf3d.html

For retail v1.1 of wolf map 1 has the following properties:
Compressed size of the first plane is 1434 which an extra 2 bytes at the start
for the the uncompressed size. The stored length of the Carmack decompressed
data is 3190, which also includes the size at the start.
"""

import io
import palette

from PIL import Image

__author__ = "Sean Donnellan"
__copyright__ = "Copyright 2020, Sean Donnellan"
__license__ = "MIT"
__version__ = "0.9.0"
__maintainer__ = "Sean Donnellan"
__email__ = "darkdonno@gmail.com"


class LevelHeader:
    def __init__(self, name, size, plane_offsets, plane_lengths):
        # The name is not really the name of the level but what is what is
        # shown in the original level editor.
        self.name = name
        self.width, self.height = size
        self.plane_offsets = plane_offsets
        self.plane_lengths = plane_lengths

    def plane(self, index):
        """The (offset, length) of the specified plane."""
        return self.plane_offsets[index], self.plane_lengths[index]

    @property
    def planes(self):
        """The (offset, length) of each plane."""
        return zip(self.plane_offsets, self.plane_lengths)

    @property
    def size(self):
        """Return the (width, height) of the level."""
        return self.width, self.height


class WallTexture:
    """The textures on the walls are naturally represented as 64 by 64 array
    of colour indices. These indices refer to a colour in the colour palette.

    For Wolf3D, the colour palette was compiled into the executable rather than
    being a separate file. An approximation for this colour palette is provided
    in the palette module.
    """

    WIDTH = 64
    HEIGHT = 64

    def __init__(self, colour_indices):
        self.colour_indices = colour_indices

    def as_rgb(self):
        return [
            colour_for_index(index)
            for index in self.colour_indices
        ]


def colour_for_index(colour_index):
    """Return the colour for the given index in the palette.

    This accounts for palette.COLOURS being a flat array of
        [red, green, blue, red, green, blue, ...]
    """
    offset = colour_index * 3
    red = palette.COLOURS[offset]
    green = palette.COLOURS[offset + 1]
    blue = palette.COLOURS[offset + 2]
    return red, green, blue


def map_headers(reader):
    """Read the map header file (MAPHEAD).

    The file format is as such:
        magic : uint16le
        level pointers : int32le (100 of them).
    """

    magic = int.from_bytes(reader.read(
        2), byteorder='little', signed=False)
    uses_rlew_compression = magic == 0xABCD
    levels = [
        int.from_bytes(reader.read(4), byteorder='little', signed=True)
        for _ in range(100)
    ]

    # Should we remove 0 and -1 where there are no levels?
    return uses_rlew_compression, levels


def level_header(reader, level_offset):
    """Read the level header from the map data file (GAMEMAPS).

    This requires an offset to the level (level_offset).

    A level is made up of up to three planes where:
    - Plane 0 is background using unmasked tiles
    - Plane 1 is foreground and uses masked tiles
    - Plane 2 is sprite/info.

    Return a LevelHeader holding the information in the header.
    """

    if level_offset == 0:
        raise StopIteration('No such level')

    def read_uint32le(reader):
        return int.from_bytes(reader.read(4), byteorder='little', signed=False)

    def read_uint16le(reader):
        return int.from_bytes(reader.read(2), byteorder='little', signed=False)

    reader.seek(level_offset)

    plane_offsets = [
        read_uint32le(reader),
        read_uint32le(reader),
        read_uint32le(reader),
    ]

    plane_lengths = [
        read_uint16le(reader),
        read_uint16le(reader),
        read_uint16le(reader),
    ]

    width = read_uint16le(reader)
    height = read_uint16le(reader)
    name = reader.read(16).split(b'\x00')[0].decode('ascii')

    # For Wolfenstein 3D there is another 4-byte string which is !ID! which
    # shows the different between v1.0 and v1.1
    signature_string = reader.read(4).decode('ascii')
    assert signature_string == '!ID!', "Expect v1.1"

    return LevelHeader(name, (width, height), plane_offsets, plane_lengths)


def decompress_carmack(data):
    """Decompress the given data using Carmack's compression algorithm.

    There are two special tags (opcode) that are kind of like instructionsthat
    power the compression:
    - Near pointers (0xA7) : count 0xA7 relative-offset (1-byte)
    - Far pointers (0xA8)  : count 0xA8, absolute-offset (2-bytes)

    count is the number of words (2-bytes) to copy.
    offsets are to a word as well.

    These essentially say repeat count words at location derived from
    the offset.

    Then there is an exception in-case the value is an opcode.
      count = 0x00, second byte of the word, first byte of the word.

    A useful resource for this was:
      http://gaarabis.free.fr/_sites/specs/files/wlspec_APB.html
    """
    data = io.BytesIO(data)

    def next_word():
        return int.from_bytes(
            data.read(2), byteorder='little', signed=False)

    uncompressed_size_in_bytes = next_word()

    assert uncompressed_size_in_bytes % 2 == 0, \
        "Expected RLEW content to be whole number of words."

    near_pointer_tag = b'\xA7'
    far_pointer_tag = b'\xA8'

    decompressed_data = bytearray()

    while True:
        count = data.read(1)
        if not count:
            break

        tag = data.read(1)

        if tag == near_pointer_tag or tag == far_pointer_tag:
            count = int.from_bytes(count, byteorder='little', signed=False)
            if count:
                if tag == near_pointer_tag:
                    # Read the relative offset.
                    value = data.read(1)
                    value = int.from_bytes(
                        value, byteorder='little', signed=False)

                    # This is applied backwards, so it means repeat count
                    # number of words from the 'value' words before the end.
                    #
                    # The shifting is converting from words to bytes (multiply
                    # by 2).
                    relative_offset = value << 1
                    offset = len(decompressed_data) - relative_offset
                else:
                    offset = data.read(2)
                    offset = int.from_bytes(
                        offset, byteorder='little', signed=False)
                    offset = offset << 1

                repeated_data = decompressed_data[offset:offset + (count << 1)]
                decompressed_data.extend(repeated_data)
            else:
                # This is the exception mentioned above where the count is 0
                # and the tag is the second byte of the word and the next
                # value is the first byte of the word.
                raise NotImplementedError()
        else:
            decompressed_data.extend(count)
            decompressed_data.extend(tag)

    assert len(decompressed_data) == uncompressed_size_in_bytes
    return decompressed_data


def decompress_rlew(data):
    """Decompress the given data using the RLEW algorithm.

    This expects the first word (two-bytes) in data is the length of the
    uncompressed data in terms of bytes.
    """
    compressed_length = len(data)
    assert compressed_length % 2 == 0, \
        "Must be divisible by 2 to be an array of words (16-bit)."

    # For Python using array.array('H', data) would be more efficient instead
    # of doing it this way.
    data = io.BytesIO(data)

    def next_word():
        return int.from_bytes(
            data.read(2), byteorder='little', signed=False)

    # This is the uncompressed length.
    uncompressed_length = next_word()

    # Remove the uncompressed length from the total length.
    compressed_length = compressed_length - 2

    # The other option is to create io.BytesIO() and write to that.
    #
    # At the moment this is instead words, which may be more useful.
    decompressed_data = []

    # This actually matches a magic number in the MAPHEAD.
    #
    # It is unclear if it is actually variable (i.e can change between
    # different files. You could imagine it might if the magic number
    # is common in the file they can choose a number that isn't common.
    compression_marker = 0xABCD

    while compressed_length > 0:
        word = next_word()
        if word == compression_marker:
            repeat_count = next_word()
            value = next_word()
            decompressed_data.extend(
                value for _ in range(repeat_count)
            )

            compressed_length -= 4
        else:
            decompressed_data.append(word)

        compressed_length -= 2

    assert len(decompressed_data) * 2 == uncompressed_length
    return decompressed_data


def read_plane(reader, plane_offset, plane_length, is_rlew_compressed):
    """Read the plane information from the map data file (GAMEMAPS).

    This requires the offset to the plane of a specific level as well
    as the length of the plane..
    """
    assert is_rlew_compressed, "untested without compression."
    reader.seek(plane_offset)
    compressed_plane_data = reader.read(plane_length)

    # Is Carmack compression used?
    # For Wolf3D v1.1 or later, the answer is yes.
    rlew_compressed_plane_data = decompress_carmack(compressed_plane_data)

    return decompress_rlew(rlew_compressed_plane_data)


def save_plane_to_image(level, plane, filename):
    tile_width, tile_height = 16, 16

    level_image = Image.new('RGB', (level.width * tile_width,
                                    level.height * tile_height))

    def row_column():
        for row in range(level.height):
            for column in range(level.width):
                yield row, column

    for (row, column), tile_index in zip(row_column(), plane):
        # Map the tile to a colour for now.
        tile = (tile_index, tile_index, tile_index)
        level_image.paste(tile, (column * tile_width, row * tile_height,
                                (column + 1) * tile_width,
                                (row + 1) * tile_height))

    level_image.save(filename, 'PNG')


def read_video_swap(reader):
    """Read the VSWAP.WL6 which contains the wall tiles.

    struct Header
    {
        uint16_t ChunkCount;
        uint16_t SpriteStart;
        uint16_t SoundStart;
        uint32_t ChunkOffsets[ChunkCount];
        uint16_t ChunkLengths[ChunkCount];
    };

    The SpriteStart and SoundStart are the indices in the chunks.
    The chunks are: [walls, sprites, sounds]
    """
    chunk_count = int.from_bytes(
        reader.read(2), byteorder='little', signed=False)
    sprite_start = int.from_bytes(
        reader.read(2), byteorder='little', signed=False)
    sound_start = int.from_bytes(
        reader.read(2), byteorder='little', signed=False)
    assert sprite_start < sound_start

    chunk_offsets = [
        int.from_bytes(reader.read(4), byteorder='little', signed=False)
        for _ in range(chunk_count)
        ]

    chunk_lengths = [
        int.from_bytes(reader.read(2), byteorder='little', signed=False)
        for _ in range(chunk_count)
        ]

    chunks = list(zip(chunk_offsets, chunk_lengths))
    # for index, (offset, length) in enumerate(chunks):
    #     print('Wall' if index < sprite_start else
    #           ('Sprite' if index  < sound_start else 'Sound'))

    walls = []

    wall_chunks = chunks[:sprite_start]
    for offset, length in wall_chunks:
        reader.seek(offset)
        wall_raw = reader.read(length)
        walls.append(WallTexture(wall_raw))

    sprites = []
    sprite_chunks = chunks[sprite_start:sound_start]
    for offset, length in sprite_chunks:
        reader.seek(offset)
        sprite_reader = io.BytesIO(reader.read(length))

        left_pixel = int.from_bytes(
            sprite_reader.read(2), byteorder='little', signed=False)
        right_pixel = int.from_bytes(
            sprite_reader.read(2), byteorder='little', signed=False)

        # Then 64 column offsets.
        column_offset = [
            int.from_bytes(
                sprite_reader.read(2), byteorder='little', signed=False)
            for _ in range(64)
            ]

        # TODO: This is incomplete.

    sounds = []
    return walls, sprites, sounds

def main():
    with open('MAPHEAD.WL6', 'rb') as reader:
        uses_rlew_compression, level_offsets = map_headers(reader)

    print('Level count: %s' % sum(1 for level in level_offsets if level > 0))

    with open('VSWAP.WL6', 'rb') as reader:
        walls, sprites, sounds = read_video_swap(reader)

    # Save out the wall textures to individual PNG files.
    #
    # It might actually be possible for Pillow to handle this via its
    # ImagePalette option.
    for i, wall in enumerate(walls):
        wall_image = Image.new('RGB', (64, 64))
        # Pillow starts at upper left as (0, 0) where the data is bottom left.
        wall_image.putdata(wall.as_rgb())
        wall_image= wall_image.transpose(Image.ROTATE_270)
        wall_image.save('wolf3d_wall_%d.png' % i)

    with open('GAMEMAPS.WL6', 'rb') as f:
        magic = f.read(8)
        assert magic == b'TED5v1.0'

        for level_index, level_offset in enumerate(level_offsets):
            if level_offset == 0:
                break

            level = level_header(f, level_offset)
            offset_to_plane_0, length_of_plane_0 = level.plane(0)
            plane = read_plane(f, offset_to_plane_0, length_of_plane_0,
                               uses_rlew_compression)

            save_plane_to_image(
                level, plane,
                filename='wolf3d_level_%d.png' % (level_index + 1))

if __name__ == '__main__':
    main()
