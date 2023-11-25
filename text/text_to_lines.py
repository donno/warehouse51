"""Convert text to a polylines that represents that text.

This uses Harfbuzz though the Python binding uharfbuzz.

A simple demo which hooks this up to Skia to draw would also be nice.
"""

__author__ = "Sean Donnellan"
__copyright__ = "Copyright (C) 2023 Sean Donnellan"
__version__ = "0.2.0"

import uharfbuzz
import os


class Font:
    """Represent a TrueType font.

    A font is  a digital data file containing a set of graphically related
    glyphs.
    """
    def __init__(self, font_path):
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

        with open(font_path, "rb") as reader:
            font_data = reader.read()

        # Load the font.
        face = uharfbuzz.Face(font_data)
        font = uharfbuzz.Font(face)
        font.scale = (face.upem, face.upem)
        uharfbuzz.ot_font_set_funcs(font)
        self._hbfont = font

    @property
    def harfbuzz_font(self):
        return self._hbfont

    @property
    def extents(self):
       return self.harfbuzz_font.get_font_extents('ltr')

    def shape(self, text: str):
        """Shapes a text

        This shapes a piece of text.

        Read https://harfbuzz.github.io/shaping-and-shape-plans.html for
        details.

        Arguments
        ---------
        text
            A string of text to shape.

        Returns
        -------
        Buffer
            A harfbuzz buffer object.
        """
        buffer = uharfbuzz.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        uharfbuzz.shape(self.harfbuzz_font, buffer, features=None,
                        shapers=None)
        return buffer


class Lines:
    """Represent a series of lines.

    The lines are represented as the points with an offset applied.
    """
    def __init__(self, offset_x, offset_y):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self._current_line = []
        self._lines = []

    def __len__(self):
        return len(self._lines)

    def __iter__(self):
        return iter(self._lines)

    def add_to_current_line(self, x, y):
        point = (x + self.offset_x, y + self.offset_y)
        return self._current_line.append(point)

    def close_current_line(self):
        self._current_line.append(self._current_line[0])
        self._lines.append(self._current_line)
        self._current_line = []


def draw_functions():
    """The draw functions build a series of line segments using Lines."""

    def move_to(x, y, lines):
        # This takes the pen off the paper and starts a new line.
        if lines._current_line:
            raise NotImplementedError("NYI move_to in the middle of a line")

        lines.add_to_current_line(x, y)

    def line_to(x, y, lines):
        lines.add_to_current_line(x, y)

    def cubic_to(c1x, c1y, c2x, c2y, x, y, lines):
        #buffer_list.append(f"C{c1x},{c1y} {c2x},{c2y} {x},{y}")
        # TODO: Ignore the control points just put the line point.
        # The idea would be to smooth the curve and generate N points along it.
        lines.add_to_current_line(x, y)

    def quadratic_to(c1x, c1y, x, y, lines):
        #buffer_list.append(f"Q{c1x},{c1y} {x},{y}")
        # TODO: Ignore the control points just put the line point.
        # The idea would be to smooth the curve and generate N points along it.
        lines.add_to_current_line(x, y)

    functions = uharfbuzz.DrawFuncs()
    functions.set_move_to_func(move_to)
    functions.set_line_to_func(line_to)
    functions.set_cubic_to_func(cubic_to)
    functions.set_quadratic_to_func(quadratic_to)
    functions.set_close_path_func(Lines.close_current_line)
    return functions


def text_to_lines_per_glyph(font: Font, text: str):
    """For each glyph in text a collection of lines will be produced.
    """
    buffer = font.shape(text)
    y_cursor = -font.extents.descender
    x_cursor = 0

    draw_funcs = draw_functions()

    for info, pos in zip(buffer.glyph_infos, buffer.glyph_positions):
        lines = Lines(x_cursor + pos.x_offset, y_cursor + pos.y_offset)
        font.harfbuzz_font.draw_glyph(info.codepoint, draw_funcs, lines)

        # Only yield lines if there are lines for the glyph.
        if lines:
            yield lines

        x_cursor += pos.x_advance
        y_cursor += pos.y_advance


def text_to_points_for_each_line(font: Font, text: str):
    """Yields the points for each line so multiple lines will make up a glyph.

    This is not useful if you want to colour each glyph separately as you won't
    know what glyph the line belongs to.
    """
    for lines in text_to_lines_per_glyph(font, text):
        for line in lines:
            yield line
