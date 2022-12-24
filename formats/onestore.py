"""A module for working with files in the OneNote Revision Store File Format.

This is described by the specification [MS-ONESTORE].
https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-onestore/

This format doesn't seem to match the OneNote 2007 format which is what I was
interested in, as such this likely will remain incredibly incomplete and
abandoned.
"""

# It would most likely be beneficial to use https://kaitai.io/ to document
# the format and produce a parser for Python. Alternatively, I have used the
# construct package (https://github.com/construct/construct/) before.

import enum
import struct


class GuidFileType(enum.Enum):
    """The GUID for the file type as specified by [MS-DTYP].

    For [MS-ONESTORE] it must be one of these first two types.

    However, it seems like the GUID for 2007 should also work.
    """

    ONE = "{7B5C52E4-D88C-4DA7-AEB1-5378D02996D3}"
    ONE_TOC_2 = "{43FF2FA1-EFD9-4C76-9EE2-10EA5722765F}"

    # Source: http://justsolve.archiveteam.org/wiki/OneNote
    ONE_2007 = "{E4525C7B-8CD8-A74D-AEB1-5378D02996D3}"

    @classmethod
    def from_bytes(cls, value):
        if len(value) != 16:
            raise ValueError('There must be exactly 16 bytes')

        for enumerant in cls:
            hex_string = enumerant.value[1:-1].replace('-', '')
            if value == bytes.fromhex(hex_string):
                return enumerant

        raise ValueError(f'Unexpected GUID for the file type: {value.hex()}')


class Guid:
    def __init__(self, raw_bytes):
        self.raw = raw_bytes

    def __str__(self):
        """Format the GUID using Microsoft's typical format.
        """
        hex = self.raw.hex().upper()
        return f'{{{hex[:8]}-{hex[8:12]}-{hex[12:16]}-{hex[16:]}}}'


class FileChunkReference64x32:
    """File chunk reference.

    This is essentially the offset and the size.

    stp (8 bytes): An unsigned integer that specifies the location of the
    referenced data in the file.
    cb (4 bytes): An unsigned integer that specifies the size, in bytes, of the
    referenced data.
    """

    def __init__(self, raw_bytes):
        self.raw = raw_bytes
        self.stp, self.cb = struct.unpack_from("<QI", raw_bytes)

    def __str__(self) -> str:
        return f'FileChunkReference64x32({self.stp}, {self.cb})'

    @property
    def offset(self):
        return self.stp

    @property
    def size(self):
        return self.cb


class Header:
    """The Header structure MUST be at the beginning of the file."""

    def __init__(self, reader):
        self.data = reader.read(1024)

    @property
    def guid_file_type(self):
        """The GUID that represents the file type.

        This is the first 16 bytes of the header.
        """
        print(self.data[:16].hex())
        return GuidFileType.from_bytes(self.data[:16])

    @property
    def guid_file(self):
        """The GUID that represents the file.
        """
        return Guid(self.data[16:32])

    @property
    def guid_legacy_file_version(self):
        """The GUID that represents the legacy file version.

        This is MUST be "{00000000-0000-0000-0000-000000000000}" and
        MUST be ignored.
        """
        guid = self.data[32:48]
        if guid != bytes([0] * 16):
            raise ValueError('The legacy file version must be all zeroes.')
        return Guid(guid)


    @property
    def guid_file_format(self):
        """The GUID that represents the format of the file.
        """
        return Guid(self.data[48:64])

    @property
    def file_node_list_root_reference(self):
        """The reference to the root of the file node list.

        This is of type FileChunkReference64x32.

        In the specification this is fcrFileNodeListRoot.

        This is 12-bytes and it must not be be "fcrZero" or "fcrNil".
        """
        return FileChunkReference64x32(self.data[172:184])


def read_file_List(header, reader):
    reference = header.file_node_list_root_reference
    reader.seek(reference.offset)
    data = reader.read(reference.size)

    # data starts with FileNodeListHeader (2.4.2).
    magic, file_node_list_id, fragment_sequence_count = struct.unpack_from(
        "<QII", data)

    if magic != 0xA4567AB1F5F7F4C4:
        raise ValueError(
            'FileNodeListHeader did not start with the magic number.')

    if file_node_list_id < 0x00000010:
        raise ValueError(
            'FileNodeListID must be equal to or greater than 0x00000010.')

    # fragment_sequence_count must be 0 for the first fragment in a file node
    # list and the rest must be sequential
    print(fragment_sequence_count)


if __name__ == '__main__':
    with open('Quick Notes.one', 'rb') as reader:
        header = Header(reader)

        # A GUID, as specified by [MS-DTYP], that specifies that the file is a
        # revision store file. MUST be "{109ADD3F-911B-49F5-A5D0-1791EDC8AED8}"
        # This is not what I get.
        print(header.guid_file_type)

        # The root file node list (section 2.1.14) is the file node list that
        # is the root of the tree of all file node lists in the file.
        print(header.file_node_list_root_reference)

        read_file_List(header, reader)
