"""A module for working with Minix file system.

This is primarily intended to be a learning aid.

Reading a real file-system image:
- Prepare in Alpine Linux a 25MB image that is formatted with the Minix file
  system.
    ```
    apk add util-linux-misc
    dd if=/dev/zero of=minixfs.raw bs=256K count=100
    losetup /dev/loop1 minixfs.raw
    mkfs.minix -1 /dev/loop0

    [ ! -d /media/minix ] && mkdir /media/minix
    # This part doesn't work from Alpine, I ended up using a VM With
    # Ubuntu Server in live mode (and needed to mount to loop7 as that was the
    # first free one.)
    # mount /dev/loop0 /media/minix
    # umount /media/minix

    losetup -d /dev/loop0

- When the image is mounted create several folders and files.
  ```
  mkdir system users media
  mkdir users/dick users/erik users/jim users/ast media/audio media/videos
  mkdir system/bin system/lib system/etc system/var
  touch system/bin/sh system/bin/ls system/bin/rm system/bin/ping system/bin/tar
  touch media/videos/big-buck-bunny.mkv media/audio/fur-elise.mid
  echo "Hello" > users/ast/welcome
  echo -e "OS: Design and Implementation\nTo Kill a Mocking Bird" >> users/ast/books
  ```

Output
    8544 inodes
    25600 blocks
    Firstdatazone=275 (275)
    Zonesize=1024
    Maxsize=268966912

Disk layout

- First block is boot block
- second block is the super block (at offset 1024)
- I-node map (there are super_block.zone_map_block_count number of blocks.
- Zone map (there are super_block.zone_map_block_count number of blocks.
- I-Nodes - (inode count + i-nodes per-block - 1) / i-nodes per block
- ...
- data zones  (zone count - first data size) <<< log_zone_size.

"""

import enum
import pathlib
import struct
import typing
from dataclasses import dataclass


INODE_SIZE: int = 32
"""The size of a i-node on disk in bytes."""

BLOCK_SIZE: int = 1024
"""The size of a block in bytes."""

INODES_PER_BLOCK: int = BLOCK_SIZE // INODE_SIZE
"""The size of a block in bytes."""

ROOT_INODE: int = 1
"""The i-node number for the root i-node."""


def _read_short(reader: typing.IO[bytes]) -> int:
    """Read an unsigned short from the reader."""
    return int.from_bytes(reader.read(2), signed=False, byteorder="little")


def _read_long(reader: typing.IO[bytes]) -> int:
    """Read an unsigned long (32-bit) from the reader."""
    return int.from_bytes(reader.read(4), signed=False, byteorder="little")


class KnownBlockNumber(enum.IntEnum):
    """Known block numbers"""

    BOOT = 0
    SUPER = 1


class ReadWriteFlag(enum.Enum):
    READING = 0
    WRITING = 1


@dataclass
class SuperBlock:
    """Stores important information so the system can locate and understand the
    file system.

    This represents the information stored on-disk.

    For Minix, this is starts at byte 1024 from the start of the disk. This
    was done to leave room of the boot loader.
    """

    OFFSET: typing.ClassVar[int] = 1024
    """The offset of the super block from the start of a disk."""

    SIZE: typing.ClassVar[int] = 1024
    """The offset of the super block from the start of a disk."""

    MAGIC: typing.ClassVar[int] = 0x137F
    """The magic number contained in super block.

    Other constants are: 0x2468 for V2 and 0x4d5a for V3.
    """

    inode_count: int
    """The total number of i-nodes.
    """
    # TODO: Document how this is determined.

    zone_count: int
    """The total number of zones.

    This must be at least 5 blocks.
    """
    # TODO: Document how this is determined.

    inode_map_block_count: int
    zone_map_block_count: int
    first_zone: int

    log_zone_size: int
    """The log2 of block/size."""

    file_size_max: int
    """The maximum size (in bytes) of a single file."""

    magic: int
    """The magic number that represents this file system."""

    state: int
    """The mount state.

    This indicates if it was cleanly unmounted.

    First bit is 0 if dirty and 1 if cleaning unmounted.
    """

    @property
    def cleanly_unmounted(self) -> bool:
        return self.state & (1 << 0) == 1

    @classmethod
    def from_reader(cls, reader: typing.IO[bytes]):
        # The alternative to this approach is to use the `struct` module
        # instead.
        inode_count = _read_short(reader)
        zone_count = _read_short(reader)
        return cls(
            inode_count,
            zone_count,
            _read_short(reader),
            _read_short(reader),
            _read_short(reader),  # First zone
            _read_short(reader),
            _read_long(reader),
            _read_short(reader),
            _read_short(reader),
        )


INODE_TYPE_MASK: int = 0o0170000
# define I_TYPE          0170000	/* this field gives inode type */


class ModeFlags(enum.IntFlag):
    # Types
    REGULAR = 0o0100000
    BLOCK_SPECIAL = 0o0060000
    DIRECTORY = 0o0040000
    """The file is a directory."""
    CHAR_SPECIAL = 0o0020000
    """This is a special character file."""

    # Protection bits # TODO: This is not right as the mode really needs to be
    # split into [user, group, other] for protection bits.
    R_BIT = 4
    W_BIT = 2
    X_BIT = 1


@dataclass
class IndexNode:
    """A node within the file system index.

    For the Minix file system, this is 32-bytes in size.

    Each value is 16-bits for total of 32-bytes
    """

    mode: int
    """16-bit integer representing the file type and RWX bits."""
    # TODO: There are several flag bits in this.

    uid: int
    """Identifies the user who owns the file."""

    file_size: int
    """The number of bytes in the file."""

    time_of_last_modification: int
    """The time (number of seconds since Jan 1, 1970) of when the file was last modified."""

    gid: int
    """The owner's group"""

    links: int

    zone_numbers: list[int]
    """The direct 7 zone numbers

    A value of 0 indicates there is no zone.
    """

    indirect: int
    double_index: int

    @property
    def is_directory(self) -> bool:
        """Return True if the index node refers to a directory."""
        return (self.mode & INODE_TYPE_MASK) == ModeFlags.DIRECTORY

    @classmethod
    def from_bytes(cls, content: bytes, offset: int = 0):
        format = "<HHLLBB7HHH"
        assert struct.calcsize(format) == INODE_SIZE, (
            struct.calcsize(format),
            INODE_SIZE,
        )
        data = struct.unpack_from(format, content, offset)
        zone_numbers = data[6:13]
        return cls(*data[:6], zone_numbers, *data[13:])


@dataclass
class DirectoryEntry:
    """Associates a filename with an inode."""

    inode_number: int
    """The corresponding i-node number for the child (file)."""

    filename: str
    """The name of the file (including if its a directory)."""


@dataclass
class Directory:
    """A node within the file system index which represents a directory.

    This includes its children.
    """

    node: IndexNode
    entries: list[DirectoryEntry]


class LoadedSystem:
    """Represented the loaded version of the Minix file system."""

    # super_block: SuperBlock

    # inode_map_blocks: list
    # # The length of this list is equal to super_block.inode_map_block_count

    def __init__(self, super_block: SuperBlock, reader: typing.IO[bytes]):
        self.super_block = super_block
        self.inode_map_blocks = []
        self.zone_map_blocks = []
        self.root_inode: IndexNode | None = None

        self._reader = reader

    @classmethod
    def from_reader(cls, reader: typing.IO[bytes]):
        reader.seek(SuperBlock.OFFSET)
        super_block = SuperBlock.from_reader(reader)

        loaded_system = cls(super_block, reader)
        loaded_system.load_bit_maps()
        loaded_system.root_inode = loaded_system.get_inode(ROOT_INODE)

        if not loaded_system.root_inode.is_directory:
            raise ValueError("The root inode should be a directory but wasn't.")

        return loaded_system

    def get_inode(self, inode_number: int):
        # TODO: There is typically an i-node cache here.
        return self.rw_inode(inode_number, ReadWriteFlag.READING)

    def rw_inode(self, inode_number: int, rw_flags: ReadWriteFlag):
        """Transfer an i-node between memory and disk.

        The steps for a read is to:
        1. Determine which block contains the required i-node
        2. Read in the block
        3. Extract the-inode and copy it to the inode table
        4. Return the block

        For writing, the entry in the inode table would be given.
        For reading, if the entry in the inode table was given it could copy
        the inode straight there.
        """

        # Rework this is it matches the OS Design and Implementation function
        # where it does both read and write, and the argument is the in-memory
        # version of the i-node where a read from disk is written and a write
        # to disk is read from.
        #
        # Otherwise, it would be better as two functions read_inode() and
        # write_inode().
        if rw_flags != ReadWriteFlag.READING:
            raise ValueError("NYI")

        # Determine which block the i-node resides in.
        block_number = (
            (inode_number - 1) // INODES_PER_BLOCK
            + self.super_block.inode_map_block_count
            + self.super_block.zone_map_block_count
            + 2
        )
        block = self.get_block(block_number)

        # TODO: Find the i-node in the block
        offset_in_block = (inode_number - 1) % INODES_PER_BLOCK
        # print(f"Relative offset in block ({block_number}): ", offset_in_block)

        offset_in_block_bytes = INODE_SIZE * offset_in_block
        # raw_data = block[offset_in_block_bytes:offset_in_block_bytes + INODE_SIZE]
        return IndexNode.from_bytes(block, offset=offset_in_block_bytes)

    def get_block(self, block_number: int):
        # Typically, there would be a cache for for the blocks loaded in,
        # however since this is is intended to simply run on an existing
        # system, rely on their file system cache instead. This may be
        # revisited later.
        self._reader.seek(BLOCK_SIZE * block_number)
        return self._reader.read(BLOCK_SIZE)

    def load_bit_maps(self):
        """Fetch the bit maps for the file system.

        This is intended to be called when the file system is loaded such as when
        it is mounted.
        """

        # Load the i-node bit map.
        for i in range(self.super_block.inode_map_block_count):
            self.inode_map_blocks.append(self.get_block(KnownBlockNumber.SUPER + 1 + i))

        # Load the i-node bit map.
        zone_offset = (
            KnownBlockNumber.SUPER + 1 + self.super_block.inode_map_block_count
        )
        for i in range(self.super_block.zone_map_block_count):
            self.zone_map_blocks.append(self.get_block(zone_offset + i))

    def read_directory(self, inode: IndexNode) -> Directory:
        """Read the directory referred to by the given inode."""
        if not inode.is_directory:
            raise ValueError("The inode should be a directory but wasn't.")

        if inode.indirect != 0:
            raise ValueError("Directories with indirect i-nodes is NYI.")
        if inode.double_index != 0:
            raise ValueError("Directories with double-index i-nodes are NYI.")

        entries = []
        for zone in inode.zone_numbers:
            block = self.get_block(zone)
            for child_inode, name in struct.iter_unpack("<H14s", block):
                if child_inode != 0:
                    terminator = name.index(b"\0")
                    name = name[:terminator]
                    entries.append(DirectoryEntry(child_inode, name))

        return Directory(inode, entries)


def open_image(path: pathlib.Path):
    """Open an image that was formatted as the Minix file system.

    For a fresh, empty Minix file system the following can be run in Alpine
    Linux to create a disk image that is 25MB and formatted as a Minix
    filesystem.

        apk add util-linux-misc
        dd if=/dev/zero of=minixfs.raw bs=256K count=100
        losetup /dev/loop0 minixfs.raw
        mkfs.minix /dev/loop0

    The information output by mkfs.minix is stored in the super block.
    """
    with path.open("rb") as reader:
        system = LoadedSystem.from_reader(reader)
        print(system.super_block)

        root_directory = system.read_directory(system.root_inode)
        print("Root I-Node", root_directory.node)
        print(
            "Root director entries:\n  " + "\n  ".join(map(str, root_directory.entries))
        )
        print(f"Cleanly unmounted: {system.super_block.cleanly_unmounted}")


if __name__ == "__main__":
    open_image(pathlib.Path.cwd() / "minixfs.raw")
