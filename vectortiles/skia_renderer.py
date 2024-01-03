"""Render vector tile from MBTiles using Skia.

This requires the skia-python package: https://pypi.org/project/skia-python/

Known issues:
- Doesn't handle points
- Doesn't handle styling - some very basic stuff has been added but is off at
  the moment.
  Possibly look at doing something inspired by https://github.com/mapbox/carto/
  If there is a Python package that handles this already that would be great.

Alternative:
    mbgl-render from https://github.com/maplibre/maplibre-native/

"""
from __future__ import annotations

import argparse
import skia
import vectortiles


class TileRenderer(vectortiles.TileVisitor):
    """Render the tile onto a Skia canvas."""

    complex_styling: bool = False
    """Configure if complex styling is used or a simplified version."""

    tile_size = 4096  # Default

    def __init__(self, canvas) -> None:
        super().__init__()
        self.layer_stack = []

        # At the moment assume everything is going to be drawn on a single
        # canvas. I don't know if skia has a type that can preserve the layers.
        self.canvas = canvas

        self.point_colour = skia.Paint(
            Color=skia.Color(15, 98, 254),
            StrokeWidth=8,
            )

        def line_paint(*rgb, stroke_width=4):
            return skia.Paint(
                AntiAlias=True,
                Style=skia.Paint.kStroke_Style,
                StrokeWidth=stroke_width,
                Color=skia.Color(*rgb),
        )

        def polygon_paint(*rgb, stroke_width=2):
            return skia.Paint(
                AntiAlias=True,
                Style=skia.Paint.kStrokeAndFill_Style,
                StrokeWidth=stroke_width,
                Color=skia.Color(*rgb),
        )

        land_colour = (252, 251, 231)

        def _scale(colour: tuple[int], scale: float) -> tuple:
            r, g, b = colour
            return int(r * scale), int(g * scale), int(b * scale)

        self.paint_for_class = {
            'river': line_paint(15, 98, 254), # Blue
            'primary': line_paint(255, 200, 89), # Orange
            'secondary': line_paint(255, 232, 115), # Yellow
            'tertiary': line_paint(255, 232, 115),
            'rail': line_paint(153, 153, 153), # Grey

            # The typical stylesheet for OSM would say do this at zoom > 12.
            'residential': polygon_paint(*_scale(land_colour, 0.98)),
            'commercial': polygon_paint(*_scale(land_colour, 0.97)),
            'industrial': polygon_paint(*_scale(land_colour, 0.96)),
            'parking': polygon_paint(238, 238, 238),

            'wood': polygon_paint(195, 217, 173),
            'lake': polygon_paint(15, 98, 254),
            'grass': polygon_paint(230, 242, 193),
            'pitch': polygon_paint(184, 230, 184), # Similar to grass.
            'stadium': polygon_paint(184, 230, 184), # Similar to grass.

            'school': polygon_paint(255, 245, 204),
            'college': polygon_paint(255, 245, 204),
            'university': polygon_paint(255, 245, 204),
        }

        self.line_paint = skia.Paint(
            AntiAlias=True,
            Style=skia.Paint.kStroke_Style,
            StrokeWidth=4,
            Color=skia.Color(255, 171, 0),
        )

        self.polygon_paint = skia.Paint(
            AntiAlias=True,
            Style=skia.Paint.kStrokeAndFill_Style,
            StrokeWidth=4,
            Color=skia.Color(171, 255, 0),
        )

    def enter_layer(self, name: str, version: int, extent: int):
        self.layer_stack.append(name)

    def leave_layer(self, name: str):
        layer = self.layer_stack.pop()
        assert layer == name, "The layer that was left should match last layer."

    def feature(self, feature_type: int, attributes: dict, geometry):
        if feature_type == vectortiles.GeometryType.POINT:
            return
            print('  Type: Point - Ignoring for now')
            command = next(geometry)
            x = command.dx
            y = command.dy

            # No idea if this is correct, but I am taking negatives to mean
            # wrap around rather than some how tracking the 'last point' draw
            # TODO: Revise this.
            if x < 0:
                x += self.tile_size
            if y < 0:
                y += self.tile_size

            #for command in geometry:
            print(command, float(command.dx), float(command.dy))
            self.canvas.drawPoint(
                float(command.dx), float(command.dy), self.point_colour)
            return

        if feature_type not in (vectortiles.GeometryType.POLYGON,
                                vectortiles.GeometryType.LINESTRING):
            raise ValueError(f'Unexpected feature type: {feature_type}')

        feature_class = attributes.get('class', None)
        if feature_class:
            feature_class = feature_class.string_value

        x = None
        y = None
        path = skia.Path()
        for command in geometry:
            if command.command_id  == vectortiles.CommandType.MOVE_TO:
                path.moveTo((command.dx, command.dy))
                x = command.dx
                y = command.dy
            elif command.command_id  == vectortiles.CommandType.LINE_TO:
                x += command.dx
                y += command.dy
                path.lineTo((x, y))
            elif command.command_id  == vectortiles.CommandType.CLOSE_PATH:
                path.close()
            else:
                raise ValueError(
                    f'Unexpected command ID ({command.command_id}).')

        if feature_type == vectortiles.GeometryType.POLYGON:
            path.close()  # Ensure it is closed.
            if self.complex_styling and feature_class:
                paint = self.paint_for_class.get(feature_class, None)
                if paint is not None:
                    self.canvas.drawPath(path, paint)
                self.canvas.drawPath(path, self.line_paint)
            else:
                self.canvas.drawPath(path, self.line_paint)
        else:
            if self.complex_styling:
                paint = self.paint_for_class.get(feature_class, self.line_paint)
                self.canvas.drawPath(path, paint)
            else:
                self.canvas.drawPath(path, self.line_paint)


def render(path: str, tile_coordinates: dict):
    width = 4096
    height = 4096
    surface = skia.Surface(width, height)
    with surface as canvas:
        tile_renderer = TileRenderer(canvas)

        with vectortiles.MBTiles(path) as src:
            assert src.meta['format'] == 'pbf'

            min_zoom, max_zoom = src.meta['minzoom'], src.meta['maxzoom']

            print(src.meta)

            if any([tile_coordinates['z'] < int(min_zoom),
                    tile_coordinates['z'] > int(max_zoom)]):
                raise ValueError("Metadata of the mbtiles file states the "
                                 f"given zoom level ({tile_coordinates['z']}) "
                                 f"is not within the file's range ({min_zoom},"
                                 f"{max_zoom})")

            tile = src.tile(**tile_coordinates)
            if tile:
                vectortiles.process_tile(
                    vectortiles.read_vector_tile(tile),
                    tile_renderer)
            else:
                raise ValueError(f"No tile {tile_coordinates}")

    image = surface.makeImageSnapshot()
    image.save('output.png', skia.kPNG)

if __name__ == '__main__':
    # A hardcoded default to make developing easier for myself.
    SOUTH_KOREA = r'G:\GeoData\Source\OpenStreetMap\derived\S_Korea.mbtiles'
    ADELAIDE = r'G:\GeoData\Generated\OpenStreetMap\adelaide-2023-12-28.mbtiles'

    parser = argparse.ArgumentParser(
        description='Render a vector tile from a mbtiles file using Skia.',
        )
    parser.add_argument(
        'mbtiles',
        nargs='?',
        help='The path to the mbtiles file.',
        default=ADELAIDE)

    parser.add_argument(
        '--zoom',
        type=int,
        default=10,
        help="The zoom level to render."
    )

    arguments = parser.parse_args()

    # TODO: Add argument to specific the tile coordinates.
    #tile_coordinates = dict(z=13, x=6987, y=5010)

    # For determining coordinates visually (rather than by going from
    # lat/long) use: https://tools.geofabrik.de/map/?grid=1#2/29.1466/31.9609
    #
    # The following is West Terrace / South Terrace of the City of Adelaide.
    #
    # This is what the wgs84_to_tile_index() confirms as well.
    # See https://gis.stackexchange.com/a/116321
    tile_coordinates = vectortiles.wgs84_to_tile_index(
        -34.927144,138.600809, zoom=arguments.zoom)

    # Both wgs84_to_tile_index() and the above produce wrong for the typical
    # MBTiles orientation, lets fix (this is where a separate class might be
    # handy that can represent either coordinates systems)
    #
    # This is noted in the MBTiles 1.3 specification:
    # > Note that in the TMS tiling scheme, the Y axis is reversed from the
    # > "XYZ" coordinate system commonly used in the URLs to request individual
    # > tiles, so the tile commonly referred to as 11/327/791 is inserted as
    # > zoom_level 11, tile_column 327, and tile_row 1256, since 1256 is
    # > 2^11 - 1 - 791.
    tile_coordinates["y"] = (
        (1 << tile_coordinates["z"]) - tile_coordinates["y"] - 1
    )


    render(arguments.mbtiles, tile_coordinates)


# Australia
# 106.4365 -44.7604 158.0176 -6.3546