"""Module for working with Mapbox GL Style JSON.

Specification: https://docs.mapbox.com/mapbox-gl-js/style-spec/

This is very much incomplete.
"""

import enum
import json

class LayerType(enum.StrEnum):
    FILL = "fill"
    """A filled polygon with an optional stroked border."""

    LINE = "line"
    """A stroked line."""

    SYMBOL = "symbol"
    """An icon or a text label."""

    CIRCLE = "circle"
    """A filled circle."""

    HEATMAP = "heatmap"
    """A heatmap."""

    FILL_EXTRUSION = "fill-extrusion"
    """An extruded (3D) polygon."""

    RASTER = "raster"
    """Raster map textures such as satellite imagery."""

    HILLSHADE = "hillshade"
    """Client-side hillshading visualization based on DEM data.

    Currently, the implementation only supports Mapbox Terrain RGB and Mapzen
    Terrarium tiles."""

    BACKGROUND = "background"
    """The background color or pattern of the map."""

    SKY = "sky"
    """A spherical dome around the map that is always rendered behind all other
    layers."""


class Style:
    """Represents a Mapbox GL Style."""
    def __init__(self, json_document):
        self.json_document = json_document

        if self['version'] != 8:
            raise ValueError('Style specification version number must be 8.')

    def __str__(self):
        return f"Style({self['name']}, v{self['version']})"

    def __getitem__(self, key):
        return self.json_document[key]

    @property
    def layers(self):
        for layer in self.json_document["layers"]:
            yield StyleLayer(layer)


class StyleLayer:
    def __init__(self, json_object):
        self.json = json_object

    def __str__(self):
        return f"Layer({self.json['id']}, {self.type})"

    @property
    def id(self) -> str:
        """Unique layer name.

        This field can not be missing.
        """
        return self.json['id']

    @property
    def type(self) -> LayerType:
        """Rendering type of this layer.

        This field can not be missing.
        """
        return LayerType(self.json['type'])

    @property
    def source_layer(self):
        """Layer to use from a vector tile source.

        Required for vector tile sources."""
        return self.json['source_layer']


if __name__ == '__main__':
    with open('osm-bright-gl-style/style.json') as reader:
        style_json = json.load(reader)

    style = Style(style_json)

    for layer in style.layers:
        if layer.type == LayerType.BACKGROUND:
            print('Background layer')
        print(layer)
        break

