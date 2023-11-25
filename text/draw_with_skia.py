"""Draw text from HarfBuzz via the uharfbuzz package to Skia.

This is meant as an aid for HarfBuzz. If you drawing text with Skia, you are
better of using its own text functions for drawing glyphs.

This is a demonstration of using that package on-top of some code I wrote.
It should be quite simple to remove the extra abstractions I added.

Known limitations
-----------------
- This draws the text upside down.

"""

# If you do have a use for the following script, feel free to remove this.
from text_to_lines import Font

import skia
import uharfbuzz


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


def render(font: Font, text: str, destination: str):
    # Setup the text render
    buffer = font.shape(text)
    y_cursor = -font.extents.descender
    x_cursor = 0
    draw_funcs = draw_functions()

    # Start drawing.
    width = sum(position.x_advance for position in buffer.glyph_positions)
    height = font.extents.ascender - font.extents.descender
    surface = skia.Surface(width, height)

    paint = skia.Paint(Color=skia.Color(15, 98, 254), StrokeWidth=2)

    with surface as canvas:
        for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
            path = skia.Path()

            font.harfbuzz_font.draw_glyph(info.codepoint, draw_funcs, path)
            canvas.translate(pos.x_offset, pos.y_offset)
            canvas.drawPath(path, paint)
            canvas.translate(-pos.x_offset, -pos.y_offset)
            canvas.translate(pos.x_advance, pos.y_advance)

            x_cursor += pos.x_advance
            y_cursor += pos.y_advance

    image = surface.makeImageSnapshot()
    image.save(destination, skia.kPNG)


if __name__ == '__main__':
    font = Font('consola.ttf')
    render(font, 'Hello World!', 'hello_world.png')
