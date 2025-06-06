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

import argparse
import dataclasses
import enum
import io
import logging
import struct
import uuid


LOG = logging.getLogger("onestore")


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


class ExtendedGuid:
    """The combination of a GUID and an unsigned integer.

    See [MS-ONESTORE] Section 2.5.1
    """
    def __init__(self, raw_bytes):
        self.guid = uuid.UUID(bytes_le=raw_bytes[:16])
        # If the GUID is all 0 then n must be 0.
        self.n = int.from_bytes(raw_bytes[16:16+4], byteorder='little')

    def __repr__(self):
        return f"{{{self.guid}}}, n={self.n}"


class FileChunkReference:
    """File chunk reference.

    This is essentially the offset and the size.

    stp (8 bytes): An unsigned integer that specifies the location of the
    referenced data in the file.
    cb (4 bytes): An unsigned integer that specifies the size, in bytes, of the
    referenced data.
    """
    def __init__(self, stp, cb):
        self.stp = stp
        self.cb = cb

    @property
    def offset(self) -> int:
        """The offset from the start of the file to the referenced data."""
        return self.stp

    @property
    def size(self) -> int:
        """The size in bytes of the referenced data."""
        return self.cb

    @property
    def end(self) -> int:
        """The offset to the end of the referenced data"""
        return self.stp + self.cb

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.stp}, {self.cb})'

    def __repr__(self):
        return f"FileChunkReference({self.stp}, {self.cb})"


class FileChunkReference64x32(FileChunkReference):
    """File chunk reference that is 64-bits and 32-bits."""

    def __init__(self, raw_bytes):
        self.raw = raw_bytes
        super().__init__(*struct.unpack_from("<QI", raw_bytes))


class Header:
    """The Header structure MUST be at the beginning of the file."""

    def __init__(self, reader):
        self.data = reader.read(1024)

    @property
    def guid_file_type(self) -> GuidFileType:
        """The GUID that represents the file type.

        This is the first 16 bytes of the header.
        """
        return GuidFileType.from_bytes(self.data[:16])

    @property
    def guid_file(self) -> Guid:
        """The GUID that represents the file.
        """
        return Guid(self.data[16:32])

    @property
    def guid_legacy_file_version(self) -> Guid:
        """The GUID that represents the legacy file version.

        This is MUST be "{00000000-0000-0000-0000-000000000000}" and
        MUST be ignored.
        """
        guid = self.data[32:48]
        if guid != bytes([0] * 16):
            raise ValueError('The legacy file version must be all zeroes.')
        return Guid(guid)

    @property
    def guid_file_format(self) -> Guid:
        """The GUID that represents the format of the file.
        """
        return Guid(self.data[48:64])

    @property
    def file_node_list_root_reference(self) -> FileChunkReference64x32:
        """The reference to the root of the file node list.

        This is of type FileChunkReference64x32.

        In the specification this is fcrFileNodeListRoot.

        This is 12-bytes and it must not be be "fcrZero" or "fcrNil".
        """
        return FileChunkReference64x32(self.data[172:184])


def file_node_id_to_type_name(node_id: int):
    """The FileNode ID field is describes the type of the file node.

    The list of values that follows come from [MS-ONESTORE] 2.4.3.

    This returns the name and base-type.
    """
    mapping = {
        0x004: (0, "ObjectSpaceManifestRootFND"),
        0x008: (2, "ObjectSpaceManifestListReferenceFND"),
        0x00C: (0, "ObjectSpaceManifestListStartFND"),
        0x010: (2, "RevisionManifestListReferenceFND"),
        0x014: (0, "RevisionManifestListStartFND"),
        0x01B: (0, "RevisionManifestStart4FND"),
        0x01C: (0, "RevisionManifestEndFND"),
        0x01E: (0, "RevisionManifestStart6FND"),
        0x01F: (0, "RevisionManifestStart7FND"),
        0x021: (0, "GlobalIdTableStartFNDX"),
        0x022: (0, "GlobalIdTableStart2FND"),
        0x024: (0, "GlobalIdTableEntryFNDX"),
        0x025: (0, "GlobalIdTableEntry2FNDX"),
        0x026: (0, "GlobalIdTableEntry3FNDX"),
        0x028: (0, "GlobalIdTableEndFNDX"),
        0x02D: (1, "ObjectDeclarationWithRefCountFNDX"),
        0x02E: (1, "ObjectDeclarationWithRefCount2FNDX"),
        0x041: (1, "ObjectRevisionWithRefCountFNDX"),
        0x042: (1, "ObjectRevisionWithRefCount2FNDX"),
        0x059: (0, "RootObjectReference2FNDX"),
        0x05A: (0, "RootObjectReference3FND"),
        0x05C: (0, "RevisionRoleDeclarationFND"),
        0x05D: (0, "RevisionRoleAndContextDeclarationFND"),
        0x072: (0, "ObjectDeclarationFileData3RefCountFND"),
        0x073: (0, "ObjectDeclarationFileData3LargeRefCountFND"),
        0x07C: (1, "ObjectDataEncryptionKeyV2FNDX"),
        0x084: (1, "ObjectInfoDependencyOverridesFND"),
        0x08C: (0, "DataSignatureGroupDefinitionFND"),
        0x090: (2, "FileDataStoreListReferenceFND"),
        0x094: (1, "FileDataStoreObjectReferenceFND"),
        0x0A4: (1, "ObjectDeclaration2RefCountFND"),
        0x0A5: (1, "ObjectDeclaration2LargeRefCountFND"),
        0x0B0: (2, "ObjectGroupListReferenceFND"),
        0x0B4: (0, "ObjectGroupStartFND"),
        0x0B8: (0, "ObjectGroupEndFND"),
        0x0C2: (1, "HashedChunkDescriptor2FND"),
        0x0C4: (1, "ReadOnlyObjectDeclaration2RefCountFND"),
        0x0C5: (1, "ReadOnlyObjectDeclaration2LargeRefCountFND"),
        0x0FF: (-1, "ChunkTerminatorFND"),
    }
    base_type, name = mapping[node_id]
    return name, base_type


class InvalidFileNode(ValueError):
    """Raised when a invalid  FileNode is encountered.

    This is a sign that there are no more file nodes.
    """


@dataclasses.dataclass
class FileNodeHeader:
    """"Defines the header at the start of a FileNode."""

    class StpFormat(enum.IntEnum):
        """The format for the stp field in FileNodeChunkReference."""
        UNCOMPRESSED_8_BYTES = 0
        UNCOMPRESSED_4_BYTES = 1
        COMPRESSED_2_BYTES = 2
        COMPRESSED_4_BYTES = 3

        def to_struct_format(self) -> str:
            """Return the corresponding format for the struct module."""
            return {
                self.UNCOMPRESSED_8_BYTES: 'Q',
                self.UNCOMPRESSED_4_BYTES: 'I',
                self.COMPRESSED_2_BYTES: 'H',
                self.COMPRESSED_4_BYTES: 'I',
            }[self]

    class CbFormat(enum.IntEnum):
        """The format for the cb field in FileNodeChunkReference."""
        UNCOMPRESSED_4_BYTES = 0
        UNCOMPRESSED_8_BYTES = 1
        COMPRESSED_1_BYTE = 2
        COMPRESSED_2_BYTES = 3

        def to_struct_format(self) -> str:
            """Return the corresponding format for the struct module."""
            return {
                self.UNCOMPRESSED_8_BYTES: 'Q',
                self.UNCOMPRESSED_4_BYTES: 'I',
                self.COMPRESSED_1_BYTE: 'B',
                self.COMPRESSED_2_BYTES: 'H',
            }[self]

    file_node_id: int
    """Specifies the type of the file node."""

    size: int
    """The size of the FileNode structure in bytes.

    The value encoded in the file is 13-bits.
    """

    stp_format: StpFormat
    """The size and format of the stp field of FileNodeChunkReference.

    This must be ignored if the BaseType of the file node is equal to 0.
    """

    cb_format: CbFormat
    """The size and format of the cb field of FileNodeChunkReference.

    Must be 0 and ignored if BaseType of the file node is equal to 0.
    """

    base_type: int
    """Specifies whether the structured by "fnd" in the FileNode contains a
    FileNodeChunkReference structure.

    Must be 0, 1 or 2.
    """

    @property
    def type_name(self):
        name, _ = file_node_id_to_type_name(self.file_node_id)
        return name

    @classmethod
    def from_reader(cls, reader):
        """Read the header from the reader.
        The header is a 32-bit value made up of:
        - 10 bits - FileNodeId - specifies the type.
        - 13 bits is unsigned integer with size in bytes.
        - 2-bits StpFormat
        - 2-bits CbFormat
        - 4-bits BaseType
        -  1-bit Reserved - must be 1 and be ignored.

        This is described in section 2.4.3 of the MS-ONESTORE format.

        Raises
        ------
        InvalidFileNode
            If this is not a file node (the 432-bit value is all zeros).
        """
        raw_header, = struct.unpack('<I', reader.read(4))
        if raw_header == 0:
            raise InvalidFileNode("Not a a file node.")
        if raw_header & 0x3FF == 255:
            raise InvalidFileNode("Not a a file node.")
        assert raw_header >> 31 == 1
        return cls(
            file_node_id=raw_header & 0x3FF,
            size=(raw_header >> 10) & 0x1fff,
            stp_format=cls.StpFormat((raw_header >> 23) & 0x3),
            cb_format=cls.CbFormat((raw_header >> 25) & 0x3),
            base_type=(raw_header >> 27) & 0xf,
        )


@dataclasses.dataclass
class FileNode:
    """Represents a file node"""

    header: FileNodeHeader
    """The header that describes the information about the file node."""

    data: object
    """The reference to the data."""

    children: list # These may be required to be a FIleNodeList.
    """The child nodes."""


@dataclasses.dataclass
class ObjectSpaceManifestRootFND:
    """The FileNode structure for the root object space in a revision store file.

    There must be only one of these structures and it must be in the root file
    node list.

    See [MS-ONESTORE] Section 2.5.1
    """

    gosid: ExtendedGuid
    """The identity of the object space as specified in the object space
    manifest list.

    See [MS-ONESTORE] Section 2.1.4 for object space.
    """

@dataclasses.dataclass
class ObjectSpaceManifestListReferenceFND:
    """The FileNode structure for the reference to a object space manifest list.

    See [MS-ONESTORE] Section 2.5.2
    """

    reference: FileChunkReference
    """"The reference to the object space manifest list."""

    gosid: ExtendedGuid
    """The identity of the object space as specified in the object space
    manifest list.

    See [MS-ONESTORE] Section 2.1.4 for object space.
    """


class RevisionManifestListReferenceFND:
    """The FileNode structure for the reference to a revision manifest list.

    # This contains a file node chunk reference which specifies the location
    and size of the first FileNodeListFragment in the revision manifest list.

    See [MS-ONESTORE] Section 2.5.4
    """

    FILE_NODE_ID = 0x010

    # This requires the format from the FileNodeHeader to be able to read
    # the file node chunk reference contained within.


def read_file_node_chunk_reference(
        reader,
        node_header: FileNodeHeader,
        ) -> FileChunkReference:
    """Read the FileNodeChunkReference structure that is in the reader.

    The stp_format and cb_format from node_header determines the size of the
    variables within.
    """
    format_string = '<' + node_header.stp_format.to_struct_format() + \
        node_header.cb_format.to_struct_format()
    size = struct.calcsize(format_string)
    stp, cb = struct.unpack(format_string, reader.read(size))

    # To uncompress multiple value by 8.
    if node_header.stp_format in (FileNodeHeader.StpFormat.COMPRESSED_2_BYTES,
                                  FileNodeHeader.StpFormat.COMPRESSED_4_BYTES):
        stp *= 8

    if node_header.cb_format in (FileNodeHeader.CbFormat.COMPRESSED_1_BYTE,
                                 FileNodeHeader.CbFormat.COMPRESSED_2_BYTES):
        cb *= 8

    return FileChunkReference(stp, cb)


def read_file_node(reader) -> FileNode:
    """Read a fileNode which is section 2.4.3 of the MS-ONESTORE format.

    Raises
    ------
    InvalidFileNode
        If this is not a file node (the 432-bit value is all zeros).
    """
    header = FileNodeHeader.from_reader(reader)
    if header.base_type == 0:
        # This file node does not reference any other data.
        # This also means data specified by fnd (which follows the header)
        # does not contain a reference and the two format fields should be
        # ignored.
        #
        # Often what this means is all the data is stored inline.
        if header.file_node_id == 0x004:
            guid = ExtendedGuid(reader.read(20))
            return FileNode(header, ObjectSpaceManifestRootFND(guid), [])

        message = f"Reading {header.type_name} is not yet implemented."
        raise NotImplementedError(message)
    elif header.base_type == 1:
        # The struct contains reference to data.
        # The first field of "fnd" (which follows the header) must be
        # the chunk reference.
        reference = read_file_node_chunk_reference(reader, header)
        return FileNode(header, reference, [])
    elif header.base_type == 2:
        # Contains reference to a file node list
        # First field in "fnd" (which follows the header) must be a file
        # node chunk reference that is the location of a file node list.
        reference = read_file_node_chunk_reference(reader, header)
        if header.file_node_id == 0x008:
            guid = ExtendedGuid(reader.read(20))
            data = ObjectSpaceManifestListReferenceFND(reference, guid)
            #assert header.size == 20 +size of reference. (that was 6 bytes.)
        else:
            data = reference
            raise ValueError("Situation not encountered yet")

        children = []
        current_position = reader.tell()
        # TODO: Confirm the reference is within the current fragment as
        # reader is not hte full file. additionally, it is a view onto the file
        # so any offsets from the start of the file will be wrong.

        LOG.warning("NYI - Read the node list from %s", reference)
        children.append(NotImplemented)
        # These probably should be attached to the file node.
        reader.seek(current_position)

        return FileNode(header, data, children)

    message = "The Base type for a file node is only expected to be 0, 1 or 2."
    raise ValueError(message)


def read_file_List(reader, reference: FileChunkReference):
    reader.seek(reference.offset)
    data = reader.read(reference.size)

    logger = LOG.getChild("FileNodeListFragment")
    # This is a FileNodeListFragment (2.4.1) which is the sequence of file
    # nodes from a file node list and starts with FileNodeListHeader.
    #
    # Data starts with FileNodeListHeader (2.4.2).
    # 8-bytes unsigned integer - Magic number
    # 4-bytes unsigned integer - File Node List ID
    # 4-bytes unsigned integer - Fragment Sequence Count
    #
    # There are then a sequence of FileNodes
    # There is variable amount of padding between last FieldNode and the
    # nextFragment
    #
    #  12-byte (FileChunkReference64x32)  called nextFragment.
    #  This specified if there are more fragments in this file node list and if
    # so the location and size.
    #
    # 8-bytes unsigned integer - Footer which marks the end of the
    #  FileNodeListFragment. and has a value 0x8BC215C38233BA4B.
    magic, file_node_list_id, fragment_sequence_count = struct.unpack_from(
        "<QII", data)

    if magic != 0xA4567AB1F5F7F4C4:
        raise ValueError(
            'FileNodeListHeader did not start with the magic number.')

    if file_node_list_id < 0x00000010:
        raise ValueError(
            'FileNodeListID must be equal to or greater than 0x00000010.')

    next_offset, next_size, footer = struct.unpack_from("<QIQ", data[-20:])
    if footer != 0x8BC215C38233BA4B:
        raise ValueError(
            'The FileNodeListFragment did not end with teh magic number for '
            'the footer.')

    next_fragment = FileChunkReference(next_offset, next_size)

    # fragment_sequence_count must be 0 for the first fragment in a file node
    # list and the rest must be sequential
    logger.debug("Fragment Sequence Count: %d", fragment_sequence_count)
    logger.debug("Next fragment: %s", next_fragment)

    # This is a stream of file nodes and is terminated when a certain condition
    # is met.
    # All fragments must have the same FIleNodeListID field
    with io.BytesIO(data) as chunk_reader:
        chunk_reader.read(struct.calcsize("<QII"))
        file_nodes = []
        while True:
            try:
                file_nodes.append(read_file_node(chunk_reader))
            except InvalidFileNode:
                break

        if next_fragment.size > 0:
            raise NotImplementedError("read teh next fragment.")
        return file_nodes


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path',
        help='The path to a OneNote file.',
        default='Quick Notes.one',
        nargs='?',
        )
    arguments = parser.parse_args()
    with open(arguments.path, 'rb') as reader:
        header = Header(reader)

        # A GUID, as specified by [MS-DTYP], that specifies that the file is a
        # revision store file. MUST be "{109ADD3F-911B-49F5-A5D0-1791EDC8AED8}"
        # This is not what I get.
        print("GUID File type:", header.guid_file_type)

        # The root file node list (section 2.1.14) is the file node list that
        # is the root of the tree of all file node lists in the file.
        print(header.file_node_list_root_reference)
        # Must have at least one ObjectSpaceManifestListReferenceFND.
        # Must have one object space manifest root (ObjectSpaceManifestListStartFND)
        # Zero or one FileDataStoreListReference.

        reference = header.file_node_list_root_reference
        file_nodes = read_file_List(reader, reference)
        for node in file_nodes:
            print(node)
            if node.children:
                print(node.children)
