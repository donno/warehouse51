"""Read the MineLib file format.

This is based on MineLib file format specification V1.0.
Source: http://mansci-web.uai.cl/minelib/minelib_format.pdf

Formats:
- Block-Model Descriptor File (.block)
- Block-Precedence Descriptor File (.prec)
- Optimization-Model Descriptor File
"""

import pathlib
import zipfile

import pandas


class Block:
    """Represents a block in a block model.

    This comes from a block model descriptor file.
    """

    def __init__(self, parts: list[str]):
        self.raw = parts

    def __str__(self):
        return f"Block x={self.x}, y={self.y}, z={self.z}, id={self.id}"

    @property
    def id(self):
        return self.raw[0]

    @property
    def x(self):
        return int(self.raw[1])

    @property
    def y(self):
        return int(self.raw[2])

    @property
    def z(self):
        return int(self.raw[3])

    @property
    def user_fields(self):
        return self.raw[4:]

    def __len__(self):
        return len(self.raw)


def block_model(path: pathlib.Path):
    """The block model descriptor file stores model information block-by-block.

    - Each line in the file corresponds to a block in the model.
    - All lines have the same number of columns.
    - The columns are organised as follows:
      - id - the unique identifier for the block starting with zero.
      - x, y, z - the corresponds of the block where the 0 z-coordinate
        is the bottom most shelf in the orebody.
      - str_1 to str_k represents optional user-specified fields that may
        tonnage, ore grade, or information about impurities.
    """
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            # Find blocks within it.
            block_files = [
                info for info in archive.infolist() if info.filename.endswith(".blocks")
            ]
            if len(block_files) != 1:
                error = f"Only one block file is expected in the archive not {len(block_files)}"
                raise ValueError(error)

            with archive.open(block_files[0], "r") as blocks:
                for line in blocks:
                    parts = line.decode("utf-8").split(" ")
                    parts[-1] = parts[-1].strip()
                    yield Block(parts)
    else:
        with path.open("r") as blocks:
            for line in blocks:
                yield Block(line.split(" "))


def block_model_data_frame(path: pathlib.Path):
    """Read the block model description file to a data frame.

    See block_model() for specifics about the file.
    """
    required_columns = ["ID", "X", "Y", "Z"]
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            # Find blocks within it.
            block_files = [
                info for info in archive.infolist() if info.filename.endswith(".blocks")
            ]
            if len(block_files) != 1:
                error = f"Only one block file is expected in the archive not {len(block_files)}"
                raise ValueError(error)

            with archive.open(block_files[0], "r") as blocks:
                column_count = len(blocks.readline().split(b" "))
                blocks.seek(0, 0)
                user_specified_names = [
                    f"str_{i}" for i in range(0, column_count - len(required_columns))
                ]
                column_names = required_columns + user_specified_names
                return pandas.read_csv(
                    blocks,
                    sep=" ",
                    header=0,
                    names=column_names,
                )
    else:
        with path.open("r") as blocks:
            column_count = len(blocks.readline().split(" "))
            blocks.seek(0, 0)
            user_specified_names = [
                f"str_{i}" for i in range(0, column_count - len(required_columns))
            ]
            column_names = required_columns + user_specified_names
            return pandas.read_csv(
                blocks,
                sep=" ",
                header=0,
                names=column_names,
            )


def block_precedences(path: pathlib.Path):
    """Read the block precedence file that defines relationship between blocks.

    This information is represented at the block by block level.
    Each line in the file corresponds to a block in the model and it provides
    its set of predecessors.

    The relationship is described as:
    <block ID> <predecessors count> <int p_1> ... <int p_n>

    Rules
    - All values are integers.
    - There will only be one entry for any given block.
    """
    raise NotImplementedError()


if __name__ == "__main__":
    for block in block_model(pathlib.Path.cwd() / "data" / "zuck_small.blocks.zip"):
        print(block)
        print(f"  {block.user_fields}")
        break

    blocks = block_model_data_frame(
        pathlib.Path.cwd() / "data" / "zuck_small.blocks.zip",
    )
    print(blocks)
