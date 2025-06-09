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
import typing
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

    @property
    def is_nil(self) -> bool:
        """A nil file chunk is a special value.

        It specifies a file chunk reference where all bits of the stp field
        are set to 1, and all bits of the cb field are set to zero.
        """
        # TODO: Check if the compressed version handles this.
        return self.stp == 0xffffffffffffffff and self.cb == 0

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

    def is_file_node(self, file_node_class: type | tuple[type]):
        if isinstance(file_node_class, tuple):
            return any(self.file_node_id == node_class.FILE_NODE_ID
                       for node_class in file_node_class)
        return self.file_node_id == file_node_class.FILE_NODE_ID

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
        if raw_header == 0 or raw_header & 0x3FF == 0:
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

    header: FileNodeHeader = dataclasses.field(repr=False)
    """The header that describes the information about the file node."""

    data: object
    """The reference to the data."""

    children: list['FileNode'] = dataclasses.field(repr=False)
    """The child nodes."""


@dataclasses.dataclass
class GlobalIdTableStart2FND:
    """Specifies the beginning of the global identification table.

    This contains no data.

    This is applicable to the .one file format.

    There must be:
     * Zero ore more FileNode with a value 0x024 (GlobalIdTableEntryFNDX)
     * A FileNode with value 0x028 (GlobalIdTableEndFNDX).

    See [MS-ONESTORE] Section 2.5.3
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x022
    """The ID of this type of file node."""


@dataclasses.dataclass
class GlobalIdTableEndFNDX:
    """Specifies the end of the global identification table.

    This contains no data.

    See [MS-ONESTORE] Section 2.1.3 and 2.4.3.
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x028
    """The ID of this type of file node."""


@dataclasses.dataclass
class GlobalIdTableEntryFNDX:
    """"Specifies an entry in the current global identification table.

    See [MS-ONESTORE] Section 2.5.10
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x024
    """The ID of this type of file node."""

    index: int
    """AN unsigned integer that specifies the index of the entry.

    Constraints:
    - Must be less than 0xFFFFFF
    - Must be unique relative to other indices in this table and those of the
      other three tables (FNDX, 2FNDX and 3FNDX).
    """

    guid: Guid
    """A GUID as specified by [MDS-DTYP]

    Constraints
    - Must not be all zeros
    - Must be unique relative to other GUID fields in this global
      identification table.
    """


@dataclasses.dataclass
class RootObjectReference3FND:
    """"Specifies the root object of a revision for a particular root role.

    See [MS-ONESTORE] Section 2.5.16
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x05A
    """The ID of this type of file node."""

    object_id_root: ExtendedGuid
    """Specifies the identity of the root object of the containing revision for
    the role specified by the RootRole field.
    """

    root_role: int
    """An unsigned integer that specifies the role of the root object."""


@dataclasses.dataclass
class RevisionRoleDeclarationFND:
    """"Specifies a new additional revision role value to associate with a
    revision.

    The revision role label is in the default context.

    See [MS-ONESTORE] Section 2.5.17
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x05C
    """The ID of this type of file node."""

    revision_id: ExtendedGuid
    """Specifies the identity of the revision to add the revision role to.

    It must match the value of the revision_id field of the preceding
    RevisionManifestStart4FND, RevisionManifestStart6FND or
    RevisionManifestStart7FND of one of preceding revision manifests
    """

    root_role: int
    """Specifies a revision role for the default context.."""


@dataclasses.dataclass
class RevisionRoleAndContextDeclarationFND:
    """"Specifies a new additional revision role and context pair to associate
    with a revision.

    See [MS-ONESTORE] Section 2.5.18
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x05D
    """The ID of this type of file node."""

    base: RevisionRoleDeclarationFND
    """Specifies the revision and revision role."""

    context_id: ExtendedGuid
    """Specifies the context that labels this revision."""


@dataclasses.dataclass
class ObjectSpaceManifestRootFND:
    """The FileNode structure for the root object space in a revision store file.

    There must be only one of these structures and it must be in the root file
    node list.

    See [MS-ONESTORE] Section 2.5.1
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x004
    """The ID of this type of file node."""

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

    FILE_NODE_ID: typing.ClassVar[int] = 0x008
    """The ID of this type of file node."""

    reference: FileChunkReference
    """"The reference to the object space manifest list."""

    gosid: ExtendedGuid
    """The identity of the object space as specified in the object space
    manifest list.

    See [MS-ONESTORE] Section 2.1.4 for object space.
    """


@dataclasses.dataclass
class ObjectSpaceManifestListStartFND:
    """The FileNode structure that specifies the beginning of an object space
    manifest list.

    See [MS-ONESTORE] Section 2.5.3
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x00C
    """The ID of this type of file node."""

    gosid: ExtendedGuid
    """The identity of the object space as specified in the object space
    manifest list.

    See [MS-ONESTORE] Section 2.1.4 for object space.
    """


@dataclasses.dataclass
class RevisionManifestListReferenceFND:
    """The FileNode structure for the reference to a revision manifest list.

    This contains a file node chunk reference which specifies the location
    and size of the first FileNodeListFragment in the revision manifest list.

    See [MS-ONESTORE] Section 2.5.4
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x010
    """The ID of this type of file node."""

    reference: FileChunkReference
    """"The reference to the object space manifest list."""


@dataclasses.dataclass
class RevisionManifestListStartFND:
    """The FileNode structure for the reference to a revision manifest list.

    See [MS-ONESTORE] Section 2.5.5
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x014
    """The ID of this type of file node."""

    reference: FileChunkReference
    """"The reference to the object space manifest list."""

    # It has 4-bytes which is instance_count but it must be ignored.


@dataclasses.dataclass
class RevisionManifestStart4FND:
    """The FileNode structure that specifies the beginning of a revision
    manifest.

    This revision manifest applies to the default context of the containing
    object space.

    See [MS-ONESTORE] Section 2.5.6
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x01B
    """The ID of this type of file node."""

    revision_id: ExtendedGuid
    """"The reference to the object space manifest list."""

    revision_id_dependent: ExtendedGuid
    """Specifies the identity of dependency revision.

    If this is all zero then there is no dependency revision."""

    creation_time: int
    """This is 8-btytes and is undefined and must be ignored."""

    revision_role: int
    """Specifies the revision role that labels this revision."""

    odcs_default: int
    """Specifies whether the data contained by this revision manifest is
    encrypted.

    This must be 0 and MUST be ignored.
    """


@dataclasses.dataclass
class RevisionManifestStart6FND:
    """The FileNode structure that specifies the start of the revision manifest
    for the default context of an object space.

    See [MS-ONESTORE] Section 2.5.7
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x01E
    """The ID of this type of file node."""

    revision_id: ExtendedGuid
    """Specifies the identity of this revision.

    It must be unique amongst all the other revision field of the other
    manifest start nodes"""

    revision_id_dependent: ExtendedGuid
    """Specifies the identity of dependency revision.

    If this is all zero then there is no dependency revision."""

    revision_role: int
    """Specifies the revision role that labels this revision."""

    odcs_default: int
    """Specifies whether the data contained by this revision manifest is
    encrypted.

    It must be either 0 (no encryption) or 2 (encrypted).
    """
    # TODO: enum?


@dataclasses.dataclass
class RevisionManifestStart7FND:
    """The FileNode structure that specifies the beginning of a revision manifest
    for the default context of an object space.

    See [MS-ONESTORE] Section 2.5.8
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x01F
    """The ID of this type of file node."""

    base: RevisionManifestStart6FND
    """Specifies the identity and other attributes of this revision."""

    context_id: ExtendedGuid
    """Specifies the context that labels this revision."""


@dataclasses.dataclass
class ObjectInfoDependencyOverridesFND:
    """The FileNode structure that specifies updated reference counts for objects

    The override data is specified by the ref field if the value of the
    reference field is not "fcrNil" ([MS-ONESTORE] section 2.2.4); otherwise,
    the override data is specified by the data field

    The total size of the data field, in bytes, must be less than 1024;
    otherwise, the override data must be in the location referenced by the
    reference field.

    See [MS-ONESTORE] Section 2.5.20
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x084
    """The ID of this type of file node."""

    reference: FileChunkReference
    """Specifies the location of an ObjectInfoDependencyOverrideData structure.

    If the value of this is not the nil reference value (the stp field is set
    to 1 and cb field are set to zero).
    """

    data: bytes | None
    """An optional ObjectInfoDependencyOverrideData structure.

    This specifies the updated reference counts for objects.

    It must exist if the value of reference field is not nil.
    """


@dataclasses.dataclass
class ObjectDeclaration2LargeRefCountFND:
    """The FileNode structure that specifies an object with a reference count.

    If this object is revised, all declarations of this object must specify
    identical data.

    See [MS-ONESTORE] Section 2.5.26
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x0A5
    """The ID of this type of file node."""

    blob_reference: FileChunkReference
    """Specifies a reference to an ObjectSpaceObjectPropSet structure."""

    body: 'ObjectDeclaration2Body'
    """Specifies the identity and other attributes of this object."""

    reference_count: int
    """An unsigned integer that specifies the reference count for this object.

    This is 4-bytes which is what makes it different to
    ObjectDeclaration2RefCountFND.
    """


@dataclasses.dataclass
class ReadOnlyObjectDeclaration2RefCountFND:
    """The FileNode structure that specifies an object with a reference count.

    If this object is revised, all declarations of this object must specify
    identical data.

    See [MS-ONESTORE] Section 2.5.29
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x0C4
    """The ID of this type of file node."""

    base: 'ObjectDeclaration2RefCountFND'
    """Specifies the identity and other attributes of this object.

    The values of is_property_set and is_read_only in the JCID of the body must
    be true.
    """

    md5_hash: int
    """An unsigned integer that specifies an MD5 checksum of the data
    referenced by the base.BlobRef field.

    See [RFC1321] for the checksum.

    If referenced data is encrypted it must be decrypted and padded with zeros
    to 8-byte boundary before computing the checksum.

    This is 16-bytes long.
    """


@dataclasses.dataclass
class ReadOnlyObjectDeclaration2LargeRefCountFND:
    """The FileNode structure that specifies an object with a reference count.

    If this object is revised, all declarations of this object must specify
    identical data.

    See [MS-ONESTORE] Section 2.5.30
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x0C5
    """The ID of this type of file node."""

    base: 'ObjectDeclaration2LargeRefCountFND '
    """Specifies the identity and other attributes of this object.

    The values of is_property_set and is_read_only in the JCID of the body must
    be true.
    """

    md5_hash: int
    """An unsigned integer that specifies an MD5 checksum of the data
    referenced by the base.BlobRef field.

    See [RFC1321] for the checksum.

    If referenced data is encrypted it must be decrypted and padded with zeros
    to 8-byte boundary before computing the checksum.

    This is 16-bytes long.
    """

@dataclasses.dataclass
class ObjectGroupListReferenceFND:
    """The FileNode structure that specifies a reference to an object group.

    The FileNodeId must be 0x0B0.

    See [MS-ONESTORE] Section 2.5.31
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x0B0
    """The ID of this type of file node."""

    reference: FileChunkReference
    """Specifies the location to the first FileNodeListFragment in the file node
    list for the object group."""

    object_group_id: ExtendedGuid
    """Specifies the identity of the object group that the reference field
    points to.

    It must be the same value as the object_id field in the
    ObjectGroupStartFND structure.
    """


@dataclasses.dataclass
class ObjectGroupStartFND:
    """The FileNode structure that specifies a start of an object group.

    See [MS-ONESTORE] Section 2.5.32
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x0B4
    """The ID of this type of file node."""

    object_id: ExtendedGuid
    """Specifies the identity of the object group."""


@dataclasses.dataclass
class DataSignatureGroupDefinitionFND:
    """The FileNode structure that specifies a signature for data of objects
    declared by the FileNode structures following this FileNode structure.

    # The signature's effect terminates when a FileNode structure ID equals to
    one of the following:
    - 0x0B8 (ObjectGroupEndFND structure, section 2.4.3)
    - 0x08C (DataSignatureGroupDefinitionFND structure, section 2.5.33)
    - 0x01C (RevisionManifestEndFND structure, section 2.4.3)

    See [MS-ONESTORE] Section 2.5.33
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x08C
    """The ID of this type of file node."""

    signature: ExtendedGuid
    """Specifies the signature"""


class CompactID:
    """The CompactID structure is a combination of two unsigned integers.

    A CompactID structure together with a global identification table specifies
    an ExtendedGUID structure
    """

    n: int
    """An unsigned integer that specifies the value of the ExtendedGUID.n field"""

    guid_index: int
    """An unsigned integer that specifies the index in the global
    identification table.

    The GUID that corresponds to this index provides the value for the
    ExtendedGUID.guid field.
    """


class JCID:
    """Specifies the type of object and the type of data the object contains.

    A JCID structure can be considered to be an unsigned integer of size four
    bytes as specified by property set and file data object.

    This is a 32-bit unsigned integer.
    """

    index: int
    """An unsigned integer that specified the type of object."""

    is_binary: bool
    """Specifies whether the object contains encryption data transmitted over
    the File Synchronization via SOAP over HTTP Protocol as specified in
    [MS-FSSHTTP].
    """

    is_property_set: bool
    """Specifies whether the object contains a property set."""

    is_graph_node: bool
    """Undefined and must be ignored"""

    is_file_data: bool
    """Specifies whether the object is a file data object.

    If this value is True, then the value of all the previous booleans must be
    false as well as is_read_only that follows.
    """

    is_read_only: bool
    """Specifies whether the object's data MUST NOT be changed when the object
    is revised.
    """

    reserved: int
    """11-bits that are reserved and must be zero and be ignored."""


@dataclasses.dataclass
class ObjectDeclaration2Body:
    """Specifies the identity of an object and the type of data the object contains.

    This is 9 bytes all up.

    See [MS-ONESTORE] Section 2.6.16.
    """
    object_id: CompactID
    """CompactID that specifies the identity of this object"""

    type_id: int
    """A JCID that specifies the type of data this object contains."""

    has_object_id_references: bool
    """Specifies whether this object contains references to other objects."""

    has_object_space_references: bool
    """Specifies whether this object contains references to object spaces or
    contexts.
    """

    reserved: int
    """Reserved field that is 6 bits and must be zero and is to be ignored."""

    @classmethod
    def from_reader(cls, reader) -> typing.Self:
        """Construct this class from the bytes read from reader."""
        raw_object_id = reader.read(4)
        raw_type_id = reader.read(4)
        flags = int.from_bytes(reader.read(1))

        if not hasattr(cls, '_warned'):
            LOG.warning(
                "Conversion of to CompactID and JCID NYI - this message will "
                "show once"
            )
            cls._warned = True

        return cls(
            raw_object_id,
            raw_type_id,
            flags & 1 == 1,
            flags & 2 == 2,
            flags >> 2,
        )


@dataclasses.dataclass
class ObjectDeclaration2RefCountFND:
    """Specifies an object (section 2.1.5) with a reference count.

    See [MS-ONESTORE] Section 2.5.35
    """

    FILE_NODE_ID: typing.ClassVar[int] = 0x0A4
    """The ID of this type of file node."""

    blob_reference: FileChunkReference
    """Specifies a reference to an ObjectSpaceObjectPropSet structure."""

    body: ObjectDeclaration2Body
    """Specifies the identity and other attributes of this object."""

    reference_count: int
    """An unsigned integer (1 byte) that specifies the reference count for this object."""



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


def read_file_node(reader, file_reader) -> FileNode:
    """Read a fileNode which is section 2.4.3 of the MS-ONESTORE format.

    Parameters
    ----------
    reader
        A readable binary stream containing the file chunk with the file nodes.
    file_reader
        This is the reader over the entire file, this required for reading
        file chunk references which are outside the current chunk.

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
        if header.is_file_node(ObjectSpaceManifestRootFND):
            guid = ExtendedGuid(reader.read(20))
            return FileNode(header, ObjectSpaceManifestRootFND(guid), [])
        if header.is_file_node(ObjectSpaceManifestListStartFND):
            guid = ExtendedGuid(reader.read(20))
            return FileNode(header, ObjectSpaceManifestListStartFND(guid), [])
        if header.is_file_node(RevisionManifestListStartFND):
            guid = ExtendedGuid(reader.read(20))
            instance_count = reader.read(4)
            _ = instance_count
            return FileNode(header, RevisionManifestListStartFND(guid), [])
        if header.is_file_node((RevisionManifestStart6FND,
                                RevisionManifestStart7FND)):
            guid = ExtendedGuid(reader.read(20))
            dependant_guid = ExtendedGuid(reader.read(20))
            revision_role = int.from_bytes(reader.read(4), byteorder='little')
            odcs_default = int.from_bytes(reader.read(2), byteorder='little')
            manifest = RevisionManifestStart6FND(
                guid, dependant_guid, revision_role, odcs_default,
                ),

            if header.is_file_node(RevisionManifestStart7FND):
                context_id = ExtendedGuid(reader.read(20))
                return FileNode(
                    header,
                    RevisionManifestStart7FND(manifest, context_id),
                    [],
                )
            return FileNode(header, manifest, [])

        if header.is_file_node(ObjectGroupStartFND):
            guid = ExtendedGuid(reader.read(20))
            return FileNode(header, ObjectGroupStartFND(guid), [])

        if header.is_file_node(GlobalIdTableStart2FND):
            return FileNode(header, GlobalIdTableStart2FND(), [])

        if header.is_file_node(GlobalIdTableEndFNDX):
            return FileNode(header, GlobalIdTableEndFNDX(), [])

        if header.is_file_node(GlobalIdTableEntryFNDX):
            index = int.from_bytes(reader.read(4), byteorder='little')
            guid = Guid(reader.read(16))
            return FileNode(header, GlobalIdTableEntryFNDX(index, guid), [])

        if header.is_file_node(RootObjectReference3FND):
            guid = ExtendedGuid(reader.read(20))
            root_role = int.from_bytes(reader.read(4), byteorder='little')
            return FileNode(header, RootObjectReference3FND(guid, root_role), [])

        if header.is_file_node(DataSignatureGroupDefinitionFND):
            guid = ExtendedGuid(reader.read(20))
            return FileNode(header, DataSignatureGroupDefinitionFND(guid), [])

        if header.is_file_node(RevisionManifestStart7FND):
            guid = ExtendedGuid(reader.read(20))
            dependant_guid = ExtendedGuid(reader.read(20))
            revision_role = int.from_bytes(reader.read(4), byteorder='little')
            odcs_default = int.from_bytes(reader.read(2), byteorder='little')
            return FileNode(
                header,
                RevisionManifestStart6FND(
                    guid, dependant_guid, revision_role, odcs_default,
                ),
                [],
            )

        if header.is_file_node((RevisionRoleDeclarationFND,
                                RevisionRoleAndContextDeclarationFND)):
            guid = ExtendedGuid(reader.read(20))
            revision_role = int.from_bytes(reader.read(4), byteorder='little')
            role = RevisionRoleDeclarationFND(guid, revision_role)
            if header.is_file_node(RevisionRoleAndContextDeclarationFND):
                context_id = ExtendedGuid(reader.read(20))
                return FileNode(
                    header,
                    RevisionRoleAndContextDeclarationFND(role, context_id),
                    [],
                )
            return FileNode(header, role, [])

        if header.file_node_id == 0x0B8: # ObjectGroupEndFND
            # Specifies the end of an object group and contain no data.
            return FileNode(header, None, [])

        if header.file_node_id == 0x01C: # RevisionManifestEndFND
            # Specifies the end of an revision manifest and contain no data.
            return FileNode(header, None, [])

        message = f"Reading {header.type_name} is not yet implemented."
        raise NotImplementedError(message)
    elif header.base_type == 1:
        # The struct contains reference to data.
        # The first field of "fnd" (which follows the header) must be
        # the chunk reference.
        reference = read_file_node_chunk_reference(reader, header)

        if header.is_file_node(ObjectDeclaration2RefCountFND):
            body = ObjectDeclaration2Body.from_reader(reader)
            reference_count = int.from_bytes(reader.read(1))
            data = ObjectDeclaration2RefCountFND(
                reference, body, reference_count)
        elif header.is_file_node(ObjectInfoDependencyOverridesFND):
            if reference.is_nil:
                # The data is stored inline.
                raw_data = reader.read(12)
                LOG.warning("The data is not decoded for %s", header.type_name)
                data = ObjectInfoDependencyOverridesFND(reference, raw_data)
            else:
                data = ObjectInfoDependencyOverridesFND(reference, None)
        elif header.is_file_node(ReadOnlyObjectDeclaration2RefCountFND):
            body = ObjectDeclaration2Body.from_reader(reader)
            reference_count = int.from_bytes(reader.read(1))
            base = ObjectDeclaration2RefCountFND(reference, body, reference_count)
            md5_hash = reader.read(16)
            data = ReadOnlyObjectDeclaration2RefCountFND(base, md5_hash)
        elif header.is_file_node(ReadOnlyObjectDeclaration2LargeRefCountFND):
            body = ObjectDeclaration2Body.from_reader(reader)
            reference_count = int.from_bytes(reader.read(4), byteorder='little')
            base = ObjectDeclaration2LargeRefCountFND(
                reference, body, reference_count)
            md5_hash = reader.read(16)
            data = ReadOnlyObjectDeclaration2LargeRefCountFND(base, md5_hash)
        else:
            message = f"Reading {header.type_name} is not yet implemented."
            raise NotImplementedError(message)
        return FileNode(header, data, [])
    elif header.base_type == 2:
        # Contains reference to a file node list
        # First field in "fnd" (which follows the header) must be a file
        # node chunk reference that is the location of a file node list.
        reference = read_file_node_chunk_reference(reader, header)
        if header.file_node_id == 0x008:
            guid = ExtendedGuid(reader.read(20))
            data = ObjectSpaceManifestListReferenceFND(reference, guid)
            #assert header.size == 20 +size of reference. (that was 6 bytes.)
        elif header.is_file_node(RevisionManifestListReferenceFND):
            data = RevisionManifestListReferenceFND(reference)
        elif header.is_file_node(ObjectGroupListReferenceFND):
            object_group_id = ExtendedGuid(reader.read(20))
            data = ObjectGroupListReferenceFND(reference, object_group_id)
        else:
            data = reference
            message = f"Situation not encountered yet: {header.type_name}"
            raise ValueError(message)

        children = []
        current_position = file_reader.tell()
        children.extend(read_file_List(file_reader, reference))
        file_reader.seek(current_position)
        return FileNode(header, data, children)

    message = "The Base type for a file node is only expected to be 0, 1 or 2."
    raise ValueError(message)


def read_fragment(
        reader,
        reference: FileChunkReference,
        ) -> tuple[list, FileChunkReference | None]:
    logger = LOG.getChild("FileNodeListFragment")
    logger.info(
        "Reading fragment at offset=%-8d, size=%d",
        reference.offset,
        reference.size,
        )
    reader.seek(reference.offset)
    data = reader.read(reference.size)

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
            'The FileNodeListFragment did not end with the magic number for '
            'the footer.')

    next_fragment = FileChunkReference(next_offset, next_size)

    # fragment_sequence_count must be 0 for the first fragment in a file node
    # list and the rest must be sequential
    logger.debug("Fragment Sequence Count: %d", fragment_sequence_count)
    logger.debug("Next fragment: %s",
                 next_fragment if next_fragment.size else "None")

    # This is a stream of file nodes and is terminated when a certain condition
    # is met.
    # All fragments must have the same FIleNodeListID field
    with io.BytesIO(data) as chunk_reader:
        chunk_reader.read(struct.calcsize("<QII"))
        file_nodes = []
        while True:
            try:
                file_nodes.append(read_file_node(chunk_reader, reader))
            except InvalidFileNode:
                break

        next_fragment = next_fragment if next_fragment.size > 0 else None
        return file_nodes, next_fragment


def read_file_List(reader, reference: FileChunkReference) -> list:
    file_nodes = []
    next_fragment = reference
    while next_fragment:
        nodes_from_fragment, next_fragment = read_fragment(reader,
                                                           next_fragment)
        file_nodes.extend(nodes_from_fragment)
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
            for child in node.children:
                print(f"    {child}")
                for c in child.children:
                    if c.children:
                        print(f"        {c} with {len(c.children)} children")
                    else:
                        print(f"        {c}")
