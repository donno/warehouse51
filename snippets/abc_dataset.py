"""Module for working with parquet files (metadata + meshes ) from abc-dataset.

    https://deep-geometry.github.io/abc-dataset/

This is designed to work with the parquet files from the abc-dataset that been
prepared as parquet files. These files came from
    https://huggingface.co/datasets/TimSchneider42/abc-dataset/

The script was developed against train-00037-of-02203.parquet

For metadata there is:
    https://huggingface.co/datasets/TimSchneider42/abc-dataset-meta
To use it, all the metadata can be read then the the mesh_id will correspond
to the the row in the metadata.

If you use this dataset in research etc, cite the following paper:
@InProceedings{Koch_2019_CVPR,
author = {Koch, Sebastian and Matveev, Albert and Jiang, Zhongshi and Williams, Francis and Artemov, Alexey and Burnaev, Evgeny and Alexa, Marc and Zorin, Denis and Panozzo, Daniele},
title = {ABC: A Big CAD Model Dataset For Geometric Deep Learning},
booktitle = {The IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
month = {June},
year = {2019}
}
"""

# /// script
# dependencies = [
#   "numpy",
#   "pandas",
#   "pyarrow",
# ]
# ///

import collections.abc
import dataclasses
import numpy
import pandas
import pathlib
import pyarrow.parquet


@dataclasses.dataclass
class Mesh:
    """A 3D mesh made made from the the given vertices anf facets."""

    mesh_id: int
    label: int
    vertices: numpy.ndarray
    facets: numpy.ndarray


def meshes_pandas(path: pathlib.Path) -> collections.abc.Generator[Mesh, None, None]:
    """Yield the meshes in the given parquet file using pandas."""
    frame = pandas.read_parquet(path)
    yield from meshes_dataframe(frame)


def meshes_dataframe(
    frame: pandas.DataFrame,
) -> collections.abc.Generator[Mesh, None, None]:
    """Yield the meshes in a data frame."""
    for _, series in frame.iterrows():
        yield Mesh(
            series["id"],
            series["label"],
            series["mesh.vertices"],
            series["mesh.faces"],
        )


def meshes_pyarrow(path: pathlib.Path) -> collections.abc.Generator[Mesh, None, None]:
    """Return the meshes in the given parquet file using pyarrow."""
    parquet_file = pyarrow.parquet.ParquetFile(path)
    for item in parquet_file.iter_batches():
        # TODO: SKip pandas completely, read to numpy arrays.
        frame = item.to_pandas()
        yield from meshes_dataframe(frame)


def load_metadata(path: pathlib.Path) -> pandas.DataFrame:
    """Load the metadata from the given path.

    The metadata are the 4 parquet files from:
    https://huggingface.co/datasets/TimSchneider42/abc-dataset-meta
    """
    frames = [
        pyarrow.parquet.read_table(path).to_pandas()
        for parquet_file in path.iterdir()
        if parquet_file.suffix == ".parquet"
    ]
    return pandas.concat(frames, axis=0)


if __name__ == "__main__":
    base_path = pathlib.Path(r"K:\GeoData\Source\huggingface\abc-dataset")
    metadata = load_metadata(base_path / "meta")
    single_data_file = (
        base_path
        / "782d61d4212c1410338d4571a03ac5f46fb4c48036fe7d27f8025d3d521c5187_train-00037-of-02203.parquet"
    )
    for mesh in meshes_pyarrow(single_data_file):
        mesh_metadata = metadata.iloc[mesh.mesh_id].to_dict()
        print(mesh.mesh_id)
        print(mesh.vertices)
        print(mesh.facets)
        print(mesh_metadata)
        break
