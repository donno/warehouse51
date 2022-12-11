"""Render vector tile from MBTiles using Skia.

This requires the skia-python package: https://pypi.org/project/skia-python/


Known issues:
- Doesn't handle points
- Doesn't handle styling - some very basic stuff has been added but is off at
  the moment.
  Possibly look at doing something inspired by https://github.com/mapbox/carto/
  If there is a Python package that handles this already that would be great.
"""

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
        self.layer_count = 0

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
        self.layer_count += 1
        #print(self.canvas.width)

    def leave_layer(self, name: str):
        pass

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
            print(src.meta)
            tile = src.tile(**tile_coordinates)
            if tile:
                vectortiles.process_tile(
                    vectortiles.read_vector_tile(tile),
                    tile_renderer)
            else:
                raise ValueError('No tile')

    image = surface.makeImageSnapshot()
    image.save('output.png', skia.kPNG)

if __name__ == '__main__':
    # A hardcoded default to make developing easier for myself.
    SOUTH_KOREA = r'G:\GeoData\Source\OpenStreetMap\derived\S_Korea.mbtiles'

    parser = argparse.ArgumentParser(
        description='Render a vector tile from a mbtiles file using Skia.',
        )
    parser.add_argument(
        'mbtiles',
        nargs='?',
        help='The path to the mbtiles file.',
        default=SOUTH_KOREA)

    # TODO: Add argument to specific the tile coordinates.
    tile_coordinates = dict(z=13, x=6987, y=5010)

    arguments = parser.parse_args()
    render(arguments.mbtiles, tile_coordinates)

