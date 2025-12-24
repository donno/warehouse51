"""A fsspec backend for the operating on an image of the Minix file system.

If write-support is added and it overall feature complete, then
spin this out as its own Python package with a the right entry point.

Write-support would be great as that would make it easier to write tests.


TODO:
- File access
    - cat() requires _fetch_range()
    - Alternative is provide a better file-like  returned by _open() instead of
      the abstract buffered file one. This simply has to provide io.IOBase.
- Write support - required write support in the minix module first.
"""

import operator
import pathlib

import minix
import fsspec


class MinixFileSystem(fsspec.AbstractFileSystem):
    """A backend for a disk image formatted as the Minix file system format."""

    root_marker = "/"

    def __init__(self, image_path: pathlib.Path, *args, **kwargs):
        super().__init__(args, kwargs)

        # The TarFileSystem implementation simply leaves closing the open
        # file to the garbage collector.

        self.reader = image_path.open("rb")
        self.system = minix.LoadedSystem.from_reader(self.reader)

    def ls(self, path, detail=True):

        if detail:
            entries = self.system.scandir(path)
            return sorted(
                (
                    {
                        # As per the documentation of base class, this must be
                        # the full path to the entry without protocol.
                        "name": str(entry.path),
                        "size": entry.stat().st_size,
                        "type": "directory" if entry.is_dir() else "file",
                    }
                    for entry in entries
                ),
                key=operator.itemgetter("name"),
            )

        inode = self.system._path_to_inode(pathlib.PurePosixPath(path))
        children = self.system.read_directory(inode).entries
        return sorted(child.filename.decode("utf-8") for child in children)

    def info(self, path):
        """Give details of entry at path."""
        # This avoids the behave for the base class where it queries the
        # children of the parent folder (i.e. it performs a ls() first).
        inode = self.system._path_to_inode(pathlib.PurePosixPath(path))
        if inode.is_directory:
            return {"name": path, "size": 0, "type": "directory"}
        return {"name": path, "size": inode.file_size, "type": "file"}


if __name__ == "__main__":
    fs = MinixFileSystem(pathlib.Path.cwd() / "minixfs.raw")
    for entry in fs.ls("/", detail=False):
        print(entry)

    for entry in fs.ls("/", detail=True):
        print(entry)

    print(fs.exists("/users/ast/welcome"))
    print(fs.exists("/users/ast/books"))
    print(fs.exists("/users/ast"))

    print("Is file", "Is directory")
    print(fs.isfile("/users/ast/welcome"), fs.isdir("/users/ast/welcome"))
    print(fs.isfile("/users/ast/books"), fs.isdir("/users/ast/books"))
    print(fs.isfile("/users/ast"), fs.isdir("/users/ast"))

    print(fs.stat("/users/ast/welcome"))
    print(fs.stat("/users/ast/welcome"))
    print(fs.stat("/users/ast/books"))

    print("Testing fs.walk()")
    for _, dirs, files in fs.walk("/users", detail=False):
        if files:
            print(files)
    print()

    print("Testing fs.walk('/')")
    for _, dirs, files in fs.walk("/", detail=False):
        if files:
            print(files)
    print()

    assert fs.isdir("/users")
    print("find('/users', detail=True)", fs.find("/users", detail=True))
    print("find('/users')", fs.find("/users"))
    print("Disk usage of /users", fs.disk_usage("/users", total=False))
    print("Disk usage of /users total", fs.disk_usage("/users"))
    assert fs.isdir("/")
    print("Root information", fs.info("/"))
    print("Disk usage of /", fs.disk_usage("/"))

    # TODO: Handle this
    # welcome = fs.cat_file("/users/ast/welcome")
    # print(welcome)

    # welcome = fs.cat("/users/ast/welcome")
    # print(welcome)
