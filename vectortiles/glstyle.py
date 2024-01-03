"""Module for working with Mapbox GL Style JSON.

Specification: https://docs.mapbox.com/mapbox-gl-js/style-spec/
Newer Specification: https://maplibre.org/maplibre-style-spec/

This is very much incomplete.
"""

import enum
import json
import pathlib


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

    def __getitem__(self, key: str):
        return self.json_document[key]

    @property
    def layers(self):
        for layer in self.json_document["layers"]:
            yield StyleLayer(layer)

    def layers_from_source_layer(self, source_layer_name: str):
        """Find layers given the source layer's name.

        From there the caller can account for the filter.
        """
        for layer in self.json_document["layers"]:
            source_layer = layer.get("source-layer")
            if source_layer == source_layer_name:
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

    def filter_matches(self, context):
        """Return true if the filter matches this layer given the context."""
        layer_filter = self.json["filter"]
        if len(layer_filter) == 1 and layer_filter[0] == "all":
            return True
        raise NotImplementedError("Can't handle this type of filter.")


def dev_osm_bright():
    """Development performed against OSM Bright"""
    with open('osm-bright-gl-style/style.json') as reader:
        style_json = json.load(reader)

    style = Style(style_json)

    for layer in style.layers:
        if layer.type == LayerType.BACKGROUND:
            print('Background layer')

    print("Land cover layers")
    layers = style.layers_from_source_layer("landcover")
    for layer in layers:
        # TODO: Create way to represent the filters.
        # print(layer.json["filter"])
        print(layer.json)

def dev_custom_style():
    """Development performed against style that I developed."""
    script_directory = pathlib.Path(__file__).parent
    with  open(script_directory / 'style-abs.json') as reader:
        style_json = json.load(reader)

    style = Style(style_json)
    styles_for_states = style.layers_from_source_layer(
        "states_and_territories")
    context = {}
    for layer in styles_for_states:
        # Skip it if the filter doesn't apply (this could possibly be merged
        # with the layers_from_source_layer, once its implemented.
        if not layer.filter_matches(context):
            continue

        # From here convert the "paint" to the corresponding paint object.
        if layer.type == LayerType.FILL:
            print('Fill layer')
        elif layer.type == LayerType.LINE:
            print('Line layer')
        else:
            print(f"Unexpected layer type: {layer.type}")


if __name__ == '__main__':
    #dev_osm_bright()
    dev_custom_style()