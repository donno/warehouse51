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

TODO
- Modify/write to the file system.
- Write a tool that converted a `tar` to a Minix formatted disk image.
- Separate block handling / device handling out - i.e. try a more layered
  approach
- Handle indirect and second-level indirect files.
- Handle reading part of a file and across blocks.

In-progress
- Implement fsspec over which provides a more common interface over it the
  higher level file system interface. Think of it as pathlib but for the IO.
  This is handled in separate module (minix_fsspec) .

Done
- Add a walk function to walk over the entire file system, similar to
  os.walk(). Completed 2025-12-24.
"""

import enum
import os
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
    """The file is a directory.

    This matches stat.S_IFDIR.
    """
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

    def stat(self, inode_number: int) -> os.stat_result:
        """Get the status of this file."""
        return os.stat_result(
            [
                self.mode,
                inode_number,
                None,  # Device
                self.links,
                self.uid,
                self.gid,
                self.file_size,
                0.0,  # Time of most recent access expressed in seconds..
                self.time_of_last_modification,
                self.time_of_last_modification,  # Creation time.
            ]
        )

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


class FileIO(typing.BinaryIO):
    """Represents a file from the file system as a file-like object."""

    def __init__(self, name: str, mode: str, inode: IndexNode, system: "LoadedSystem"):
        if (inode.mode & INODE_TYPE_MASK) == ModeFlags.DIRECTORY:
            # This matches what Python does on Linux, where as on Windows it is
            # a permission denied error instead.
            raise IsADirectoryError(f"Is a directory: '{name}'.")

        if (inode.mode & INODE_TYPE_MASK) != ModeFlags.REGULAR:
            raise ValueError(
                "Not a regular file - only regular files are supported for now."
            )

        if inode.indirect != 0:
            raise ValueError("File with indirect i-nodes is NYI.")
        if inode.double_index != 0:
            raise ValueError("Files with double-index i-nodes are NYI.")

        self._mode = mode
        self._name = name
        self._inode = inode
        self._inode_number = inode.number
        self._system = system
        self._closed = False
        self._position = 0

    def __repr__(self):
        if self._closed:
            return f"{self.__class__.__qualname__}(closed)"
        return (
            f"{self.__class__.__qualname__}({self._name}, inode={self._inode_number})"
        )

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def name(self) -> str:
        return self._name

    def close(self) -> None:
        """Flush and close the IO object.

        This method has no effect if the file is already closed.
        """
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def readable(self) -> bool:
        """Return whether object was opened for reading."""
        return True

    def read(self, n: int = -1) -> typing.AnyStr:
        """Read at most n characters from stream.

        Read from underlying buffer until we have n characters or we hit EOF.
        If n is negative or omitted, read until EOF.
        """
        if self.closed:
            raise ValueError("I/O operation on closed file.")

        # TODO: partial reads are NYI.
        n = self._inode.file_size if n < 0 else min(n, self._inode.file_size)
        data = self._read(position=self._position, size=n)
        self._position += n
        return data

    def _read(self, position: int, size: int) -> bytes:
        """Read the given number of bytes (size) starting at position."""
        file_size = self._inode.file_size
        if position >= file_size:
            return b""
        block_number = self._system._position_to_block_number(self._inode, position)
        block = self._system.get_block(block_number)
        if len(block) < size:
            message = f"Only reading the first block is supported ({size})"
            raise ValueError(message)

        return block[position : min(position + size, file_size)]

    def seekable(self) -> bool:
        """Return whether object supports random access.

        If False, seek(), tell() and truncate() will raise OSError.
        This method may need to do a test seek().
        """
        return True

    def seek(self, offset: int, whence: int = 0) -> int:
        """Change the stream position to the given byte offset."""
        if whence == 0:
            if offset < 0:
                message = f"negative seek position {offset}"
                raise ValueError(message)
            self._position = offset
            return self._position

        # * 1 -- current stream position; offset may be negative
        # * 2 -- end of stream; offset is usually negative
        raise ValueError("Unhandled value for whence")

    def writable(self) -> bool:
        """Return whether object was opened for writing.

        If False, write() will raise OSError.
        """
        return False

    def write(self, s: typing.AnyStr) -> int:
        raise OSError("File is not writable.")

    def __enter__(self) -> typing.IO[typing.AnyStr]:
        return self

    def __exit__(self, type, value, traceback) -> None:
        self.close()


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
                    terminator = name.find(b"\0")
                    if terminator >= 0:
                        name = name[:terminator]
                    entries.append(DirectoryEntry(child_inode, name))

        return Directory(inode, entries)

    def _path_to_inode(self, path: pathlib.PurePosixPath) -> IndexNode:
        if not path.is_absolute():
            raise ValueError("Relative paths is NYI or supported.")

        assert path.parts[0] == "/", "Only absolute paths are supported"
        parts = path.parts[1:]
        current_node = self.root_inode
        current_node.number = ROOT_INODE
        path_so_far = pathlib.PurePosixPath("/")
        for part in parts:
            children = self.read_directory(current_node).entries
            path_so_far = path_so_far / part
            try:
                part_inode_number = next(
                    child.inode_number
                    for child in children
                    if child.filename == part.encode("utf-8")
                )
            except StopIteration:
                message = f"Couldn't find {path_so_far}"
                raise FileNotFoundError(message) from None

            # Look-up the inode.
            current_node = self.get_inode(part_inode_number)
            current_node.number = part_inode_number

        return current_node

    def open(self, path: os.PathLike | str, mode: str) -> FileIO:
        """Open file and return a stream.  Raise OSError upon failure."""
        inode = self._path_to_inode(pathlib.PurePosixPath(path))
        return FileIO(path, mode, inode, self)

    def read(self, path: pathlib.PurePosixPath | str) -> bytes:
        """Read the contents of a file at the given path."""
        with self.open(path, "rb") as readable_file:
            return readable_file.read()

    def scandir(self, path: os.PathLike | str):
        """Return an iterator of DirEntry objects corresponding to the
        entries in the directory given by path.
        """
        path = pathlib.PurePosixPath(os.fspath(path))

        inode = self._path_to_inode(path)
        if not inode.is_directory:
            raise NotADirectoryError(f"The directory name is invalid: {path}")

        # This could be reworked to replace read_directory(), granted that
        # function doesn't currently need to look-up the inodes of the
        # children, so in a way it is lazier then this function.
        children = self.read_directory(inode).entries
        for child in children:
            if child.filename in (b".", b".."):
                continue
            yield DirEntry(
                path / child.filename.decode("utf-8"),
                child.inode_number,
                system=self,
            )

    def stat(self, path: os.PathLike | str) -> os.stat_result:
        """Get the status of a file or a file descriptor."""
        inode = self._path_to_inode(pathlib.PurePosixPath(path))
        # The number property is set by _path_to_inode() so it doesn't have to
        # return a pair.
        return inode.stat(inode.number)

    def _position_to_block_number(self, inode: IndexNode, position: int) -> int:
        """Given the position within the file return the block number in
        which that position is found.

        This is the block not zone number.
        """
        block_index = position // BLOCK_SIZE
        zone_index = block_index >> self.super_block.log_zone_size
        block_offset = block_index - (zone_index << self.super_block.log_zone_size)
        assert zone_index < len(inode.zone_numbers)
        zone_number = inode.zone_numbers[zone_index]
        if zone_number == 0:
            raise ValueError("No zone or block number")
        return (zone_number << self.super_block.log_zone_size) + block_offset


class DirEntry:
    """Object yielded by scandir() to expose the file path and other file attributes of a directory entry.

    This can't use os.DirEntry as that type can't be created.
    """

    def __init__(
        self, path: pathlib.PurePosixPath, inode_number: int, system: LoadedSystem
    ):
        self._path = path
        self._inode_number = inode_number
        self._system = system
        self._cached_inode: IndexNode | None = None
        self._cached_stat: os.stat_result | None = None

    @property
    def name(self) -> str:
        """The entry’s base filename, relative to the scandir() path argument."""
        return self._path.name

    @property
    def path(self) -> pathlib.PurePosixPath:
        """The entry’s full path name."""
        return self._path

    def inode(self) -> int:
        """Return the inode number of the entry."""
        return self._inode_number

    def is_file(self) -> bool:
        """Whether this path is a regular file"""
        stat = self._cache_stat()
        return (stat.st_mode & INODE_TYPE_MASK) == ModeFlags.REGULAR

    def is_dir(self) -> bool:
        """Whether this path is a directory."""
        stat = self._cache_stat()
        return (stat.st_mode & INODE_TYPE_MASK) == ModeFlags.DIRECTORY

    def stat(self):
        """Get the status of a file or a file descriptor."""
        return self._cache_stat()

    def _cache_stat(self) -> os.stat_result:
        """Cache the stat result if it not already and return it."""
        if not self._cached_stat:
            self._cached_inode = self._system.get_inode(self._inode_number)
            self._cached_stat = self._cached_inode.stat(self._inode_number)
        return self._cached_stat

    def __repr__(self):
        return f"{self.__class__.__qualname__}('{self._path}', {self.inode()})"


def walk(path: os.PathLike | str, system: LoadedSystem):
    """Directory tree generator.

    For each directory in the directory tree rooted at top (including top
    itself, but excluding '.' and '..'), yields a 3-tuple

        dirpath, dirnames, filenames
    """

    path = pathlib.PurePosixPath(os.fspath(path))

    # This is based on the os.walk() function, it would be better if it yield
    # the DirEntry items instead of the names only.
    #
    # if there was a version of scandir() that took the inode numbers or even
    # the inodes then this would be simpler as scandir() already loads the
    # IndexNode to determine if it is a directory or not.
    directories = []
    non_directories = []

    directory_iterator = system.scandir(path)
    for entry in directory_iterator:
        if entry.is_dir():
            directories.append(entry.name)
        else:
            non_directories.append(entry.name)

    # This assumes top-down.
    yield path, directories, non_directories

    for directory in directories:
        yield from walk(path / directory, system)


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
        print("Contents of /users/ast/welcome", system.read("/users/ast/welcome"))
        print("Contents of /users/ast/books", system.read("/users/ast/books"))

        for entry in system.scandir("/users/ast/"):
            print(entry, entry.is_file(), entry.is_dir())

        # Demonstration of the walk() functionality.
        for root, dirs, filenames in walk("/", system):
            print(root)
            for name in filenames:
                print(f"  {root / name}")

            # Removing an item from dirnames is meant to prevent it from
            # being searched. This is not tested/implemented.
            if "bin" in dirs:
                dirs.remove("bin")

        # Demonstrate of the open() functionality.
        with system.open("/users/ast/books", "rb") as opened_file:
            print(opened_file)
            print(opened_file.name)
            print("First read", opened_file.read())
            print("Second read", opened_file.read())
            opened_file.seek(0)
            print("After seek", opened_file.read())

            opened_file.seek(0)
            print("Read 4 bytes", opened_file.read(4))
            print("Read next 4 bytes", opened_file.read(4))
            print("Read till end", opened_file.read())

            opened_file.close()
            print("Closed", opened_file.closed)
            # print("Read after close", opened_file.read()) # Throws ValueError


if __name__ == "__main__":
    open_image(pathlib.Path.cwd() / "minixfs.raw")
