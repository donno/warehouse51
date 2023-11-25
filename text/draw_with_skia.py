"""Draw text from HarfBuzz via the uharfbuzz package to Skia.

This is meant as an aid for HarfBuzz. If you drawing text with Skia, you are
better of using its own text functions for drawing glyphs.

Known limitations
-----------------
- This draws the text upside down.
"""

import os

import skia
import uharfbuzz


def load_font(font_path: os.PathLike):
    found_font = os.path.isfile(font_path)
    if not found_font and os.path.basename(font_path) == font_path:
        # Only a filename was given, so attempt to load it from the
        # Windows font folder.
        system_font_path = os.path.join(os.environ.get('SystemRoot', ''),
                                        'fonts',
                                        font_path)
        if os.path.isfile(system_font_path):
            font_path = system_font_path
        else:
            message = f'Could not find {font_path} in current ' + \
                f'directory or at {system_font_path}'
            raise FileNotFoundError(message)
    elif not found_font:
        message = f'Could not find {font_path}'
        raise FileNotFoundError(message)

    # Load the font.
    blob = uharfbuzz.Blob.from_file_path(font_path)
    face = uharfbuzz.Face(blob)
    font = uharfbuzz.Font(face)
    font.scale = (face.upem, face.upem)
    uharfbuzz.ot_font_set_funcs(font)
    return font


def draw_functions():
    """The draw functions calls onto skia.Path functions."""
    def cubic_to(c1x, c1y, c2x, c2y, x, y, path):
        path.cubeTo(c1x, c1y, c2x, c2y, x, y)

    def quadratic_to(c1x, c1y, x, y, path):
        path.quadTo(c1x, c1y, x, y)

    functions = uharfbuzz.DrawFuncs()
    functions.set_move_to_func(lambda x, y, path: path.moveTo(x, y))
    functions.set_line_to_func(lambda x, y, path: path.lineTo(x, y))
    functions.set_cubic_to_func(cubic_to)
    functions.set_quadratic_to_func(quadratic_to)
    functions.set_close_path_func(lambda path: path.close())
    return functions


def render(harfbuzz_font, text: str, destination: str):
    # Setup the text shaper.
    buffer = uharfbuzz.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    uharfbuzz.shape(harfbuzz_font, buffer, features=None,
                    shapers=None)

    font_extents = harfbuzz_font.get_font_extents('ltr')
    y_cursor = -font_extents.descender
    x_cursor = 0
    draw_funcs = draw_functions()

    # Start drawing.
    width = sum(position.x_advance for position in buffer.glyph_positions)
    height = font_extents.ascender - font_extents.descender
    surface = skia.Surface(width, height)

    paint = skia.Paint(Color=skia.Color(15, 98, 254), StrokeWidth=2)

    with surface as canvas:
        for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
            path = skia.Path()

            harfbuzz_font.draw_glyph(info.codepoint, draw_funcs, path)
            canvas.translate(pos.x_offset, pos.y_offset)
            canvas.drawPath(path, paint)
            canvas.translate(-pos.x_offset, -pos.y_offset)
            canvas.translate(pos.x_advance, pos.y_advance)

            x_cursor += pos.x_advance
            y_cursor += pos.y_advance

    image = surface.makeImageSnapshot()
    image.save(destination, skia.kPNG)


if __name__ == '__main__':
    render(load_font('consola.ttf'), 'Hello World!', 'hello_world.png')
