"""Parse a VVRT (Virtual Raster Format) file.

This is a XML format used by GDAL (Geospatial Data Abstraction Library).

https://gdal.org/en/stable/drivers/raster/vrt.html
https://raw.githubusercontent.com/OSGeo/gdal/master/frmts/vrt/data/gdalvrt.xsd
"""

import dataclasses
import enum
import os
import pathlib

from xml.etree import ElementTree


class ColourInterpretation(enum.StrEnum):
    # TODO: Fill this out based on ColorInterpType from lvrt.xsd
    GRAY = "Gray"
    PALETTE = "Palette"


@dataclasses.dataclass
class Rectangle:
    offset_x: int
    offset_y: int
    size_x: int
    size_y: int

    @classmethod
    def from_element(cls, element: ElementTree.Element):
        return cls(
            int(element.attrib["xOff"]),
            int(element.attrib["yOff"]),
            int(element.attrib["xSize"]),
            int(element.attrib["ySize"]),
        )


class Source:
    def __init__(self, element: ElementTree.Element):
        self._element = element

    @property
    def filename(self) -> str:
        return self._element.find("./SourceFilename").text

    @property
    def band(self) -> int:
        return int(self._element.find("./SourceBand").text)

    @property
    def source_rectangle(self) -> Rectangle:
        return Rectangle.from_element(self._element.find("./SrcRect"))

    @property
    def destination_rectangle(self) -> Rectangle:
        return Rectangle.from_element(self._element.find("./DstRect"))

    @property
    def properties(self) -> dict[str, str]:
        return self._element.find("./SourceProperties").attrib

    @property
    def no_data(self) -> int:
        return self._element.find("./NODATA").text

    def __repr__(self):
        return f"<Source File={self.filename}>"


class Band:
    def __init__(self, element: ElementTree.Element):
        self._element = element

    @property
    def data_type(self) -> str:
        return self._element.attrib["dataType"]

    @property
    def band_number(self) -> int | None:
        """The band number this band represents.

        This is one based.
        """
        return int(self._element.attrib["band"])

    @property
    def no_data_value(self) -> float:
        """The value of NoData for the raster band."""
        return float(self._element.find("./NoDataValue"))

    @property
    def colour_interpretation(self) -> ColourInterpretation:
        """The type of colour interpolation to perform."""
        return ColourInterpretation(self._element.find("./ColorInterp"))

    def __repr__(self):
        return f'<VRTRasterBand dataType="{self.data_type}" band="{self.band_number}">'

    @property
    def sources(self):
        return [Source(element) for element in self._element.findall("./ComplexSource")]


class Dataset:
    def __init__(self, root: ElementTree.Element):
        self._root = root

    # Other properties:
    # - ground_control_points
    # - metadata
    # - mask_band
    # - overview_list

    @property
    def source_reference_system_wtk(self) -> str:
        """spatial reference system (coordinate system) in OGC WKT format"""
        srs = self._root.find("./SRS")
        # Attributes include:
        # - dataAxisToSRSAxisMapping
        # - coordinateEpoch
        return srs.text

    @property
    def geo_transform(self) -> str:
        """Six value affine geotransformation for the data set.

        Maps between pixel coordinates and georeferenced coordinates.
        """
        transform = self._root.find("./GeoTransform")
        values = [float(value) for value in transform.text.split(", ")]
        if len(values) != 6:
            raise ValueError("Expected transform to contain a 6 value affine.")
        return values

    @property
    def bands(self):
        return [Band(band) for band in self._root.findall("./VRTRasterBand")]


def parse(path: os.PathLike | str):
    path = pathlib.Path(os.fspath(path))
    with path.open("r") as reader:
        tree = ElementTree.parse(reader)

    root = tree.getroot()
    if root.tag != "VRTDataset":
        raise ValueError("Expected root element to be VRTDataset")

    return Dataset(root)


if __name__ == "__main__":
    dataset = parse(pathlib.Path("D:\\work\\2m_dem_tiles.vrt"))
    print(dataset.source_reference_system_wtk)
    print(dataset.geo_transform)
    print(dataset.bands)
    for source in dataset.bands[0].sources:
        # print(source.source_rectangle)
        print(source.destination_rectangle)
