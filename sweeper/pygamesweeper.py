"""Implements a frontend for the Minesweeper engine using pygame.

TODO
- Add a clock/timer
- Add a game over screen
- Add a win screen
- Maybe add high score list?
"""

import pygame
import pygame.locals

import minesweeper

# TODO: This would be something nice to standise as part of the core part that
# can be used by all users.
NUMBER_TO_COLOUR = {
    1: (0, 0, 255),
    2: (0, 255, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    # 7
    # 8
}

class PyGameEngine:
    cell_size = 64
    padding = cell_size

    def __init__(self, display):
        self.font = pygame.font.Font(None, 40)
        self.display = display
        self.restart()

        # Pre-render the numbers and pre-compute some offsets to centre
        # them. The offsets also include the top/left padding of the grid
        # purely to remove pre-compute it.
        self._number_to_text = {}
        self._number_to_offsets = {}
        for number, colour in NUMBER_TO_COLOUR.items():
            text = self.font.render(str(number), 1, (colour))
            self._number_to_text[number] = text

            text_size = text.get_size()
            self._number_to_offsets[number] = (
                self.cell_size // 2 - text_size[0] // 2 + self.padding,
                self.cell_size // 2 - text_size[1] // 2 + self.padding,
            )

        # Render the flag and maybe (question mark) using text as well.
        # Ideally the flag would get its own rendering.
        for extra, colour in [('F', (255, 0, 0)), ('?', (0, 0, 255))]:
            text = self.font.render(extra, 1, (colour))
            self._number_to_text[extra] = text

            text_size = text.get_size()
            self._number_to_offsets[extra] = (
                self.cell_size // 2 - text_size[0] // 2 + self.padding,
                self.cell_size // 2 - text_size[1] // 2 + self.padding,
            )

    @property
    def name(self):
        return "Minesweeper"

    def restart(self):
        self.field = minesweeper.beginner()

        # The colour of the field.
        field_background_colour = (112, 128, 144)

        pygame.draw.rect(
            self.display,
            field_background_colour,
            (self.padding,
             self.padding,
             self.cell_size * self.field.columns,
             self.cell_size * self.field.rows
            ))

        self._draw_grid()
        self._draw_mine_count()

    def _draw_mine_count(self):

        display_x = self.cell_size * self.field.columns + self.padding
        text = self.font.render("Mines: %3d" % self.field.remaining_mine_count,
                                1, (255, 255, 255))
        pygame.draw.rect(
            self.display,
            (0, 0, 0),
            (self.display.get_width() // 2, 0,
             self.display.get_width() // 2, self.padding))
        self.display.blit(text, (display_x - text.get_width(),
                                 text.get_height() // 2))

    def _draw_grid(self):
        padding = self.padding
        cell_size = self.cell_size
        field_x_upper = padding + cell_size * (self.field.columns)
        field_y_upper = padding + cell_size * (self.field.rows)

        for line_x in range(padding, field_x_upper + cell_size, cell_size):
            pygame.draw.line(
                self.display,
                (255, 255, 255),
                (line_x, padding),
                (line_x, field_y_upper),
                2)

        for line_y in range(padding, field_y_upper + cell_size, cell_size):
            pygame.draw.line(
                self.display,
                (255, 255, 255),
                (padding, line_y),
                (field_x_upper, line_y),
                2)

    def _fill_cell(self, row: int, column: int, colour):
        pygame.draw.rect(
            self.display,
            colour,
            (self.cell_size * column + self.padding,
             self.cell_size * row + self.padding,
             self.cell_size,
             self.cell_size))

    def _draw_flagged_cell(self, row: int, column: int, cell):
        assert cell.flag_state is not minesweeper.FlagState.OPEN
        self._fill_cell(row, column, (112, 128, 144))
        if cell.flag_state == minesweeper.FlagState.FLAG:
            text = self._number_to_text['F']
            offset = self._number_to_offsets['F']
            self.display.blit(
                text,
                (self.cell_size * column + offset[0],
                 self.cell_size * row + offset[1]))
        elif cell.flag_state == minesweeper.FlagState.MAYBE:
            text = self._number_to_text['?']
            offset = self._number_to_offsets['?']
            self.display.blit(
                text,
                (self.cell_size * column + offset[0],
                 self.cell_size * row + offset[1]))

    def _draw_cells(self):
        for row in range(self.field.rows):
            for column in range(self.field.columns):
                cell = self.field.cell(row, column)
                if cell.flag_state == minesweeper.FlagState.OPEN:
                    self._fill_cell(row, column, (128, 128, 128))
                    if cell.adjacent_mines > 0:
                        text = self._number_to_text[cell.adjacent_mines]
                        offset = self._number_to_offsets[cell.adjacent_mines]
                        self.display.blit(
                            text,
                            (self.cell_size * column + offset[0],
                             self.cell_size * row + offset[1]))

    def click(self, mouse_position, button):
        mouse_x, mouse_y = mouse_position
        column = (mouse_x - self.padding) // self.cell_size
        row = (mouse_y - self.padding) // self.cell_size

        # Check if the user clicked outside the play area.
        if row < 0 or row >= self.field.columns:
            return

        if column < 0 or column >= self.field.rows:
            return

        if button == 1:
            self.field.pick(row, column)
            self._draw_cells()
            self._draw_grid()
        else:
            # NOTE: if flag and pick returned if there was any change that
            # would help. Or maybe they should return what cells were changed.
            cell = self.field.flag(row, column)
            if cell.flag_state is not minesweeper.FlagState.OPEN:
                self._draw_mine_count()
                self._draw_flagged_cell(row, column, cell)

                # Consider drawing the grid around the cell.
                self._draw_grid()


def main():
    pygame.init()

    display = pygame.display.set_mode((704, 704), 0, 32)
    engine = PyGameEngine(display)

    pygame.display.set_caption(engine.name)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYUP:
                if event.key == pygame.locals.K_r:
                    engine.restart()
            elif event.type == pygame.MOUSEBUTTONUP:
                engine.click(event.pos, event.button)
        pygame.display.update()


if __name__ == '__main__':
    main()
