"""An implementation of the old classic game, Minesweeper.

The objective is to pick cells in a grid where you don't believe there is a
mine (bomb). If you pick incorrectly you loose the game because the mine goes
off (it explodes).

TODO
- Add a clock/timer?
- Add handling for intergrating a user interface.
"""

import enum
import itertools
import random

__version__ = '0.3.0'
__copyright__ = "Copyright 2019, https://github.com/donno/"


class GameOver(ValueError):
    def __init__(self):
        super().__init__("You picked a cell which had a mine in it.\n"
                         "Better luck next time.")


class FlagState(enum.Enum):
    """The user has not placed a flag nor opened it."""
    NONE = 0

    """The user has placed a flag as a warning."""
    FLAG = 2

    """The user has flagged the area as a maybe."""
    MAYBE = 3

    """There is no flag here because the user has opened it up."""
    OPEN = 4


class Cell:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.flag_state = FlagState.NONE

        """The number of mines next to this cell."""
        self.adjacent_mines = 0

        self.has_mine = False

    @property
    def cleared(self):
        """Return true if the area has been cleared."""
        assert not self.has_mine, "How is it cleared if there is a mine"
        return self.flag_state == FlagState.OPEN

    def __repr__(self):
        representation = {
            FlagState.NONE: ' ',
            FlagState.FLAG: 'F',
            FlagState.MAYBE: '?',
            FlagState.OPEN: str(self.adjacent_mines),
        }
        return representation[self.flag_state]


class MineField:
    def __init__(self, rows: int, columns: int, mines: int):
        """"
        Parameters
        ----------
        rows
            The number of rows in the grid where there may be mines.
        columns
            The number of columns in the grid where there may be mines.
        mines
            The number of mines in the grid.
        """
        self.rows = rows
        self.columns = columns
        self.mines = mines
        self.cells = list(Cell() for _ in range(0, self.rows * self.columns))

        # Keep track of if the locations of the mines have been chosen.
        self._chosen = False

    def pick(self, row: int, column: int):
        """"Pick a (row, column) as being safe for a mine.

        Parameters
        ----------
        row
            The row in the grid/field to pick in.
        column
            The column in the grid/field to pick in.

        Raises
        ------
        GameOver
            If there was a mine at the location picked.
        """

        if not self._chosen:
            self._lay_mines(row, column)
            self._chosen = True
            # This is where you would normally start a clock/timer.

        self._clear_mines(row, column)
        return self.cell(row, column)

    def flag(self, row: int, column: int):
        """"Place a flag at(row, column) if the cell isn't already opened.
        If there is a flag then it will be changed to a maybe (question mark).
        If there is a maybe then it is changed to none (i.e initial state).

        Parameters
        ----------
        row
            The row in the grid/field to flag.
        column
            The column in the grid/field to flag.
        """

        # In the Windows 7 version of Minesweeper the timer doesn't start if
        # you flag cells.

        cell = self.cell(row, column)
        if cell.flag_state == FlagState.NONE:
            cell.flag_state = FlagState.FLAG
        elif cell.flag_state == FlagState.FLAG:
            cell.flag_state = FlagState.MAYBE
        elif cell.flag_state == FlagState.MAYBE:
            cell.flag_state = FlagState.NONE

        return cell

    def cell(self, row: int, column: int):
        if row < 0 or column < 0:
            raise IndexError()

        if row >= self.rows or column >= self.columns:
            raise IndexError()

        return self.cells[column + self.columns * row]

    @property
    def remaining_mine_count(self):
        """The number of mines that are remaining.

        This is based on the flags the user has placed to mark mines and it
        doesn't take into account if they are correct. This is by-design and
        not a bug.
        """
        return self.mines - sum(1 for cell in self.cells
                                if cell.flag_state == FlagState.FLAG)

    def _lay_mines(self, row: int, column: int):
        """Mines are only laid after the first pick.

        This avoids instant failure. There can't be a mine at start.

        Ideally, a good minesweeper game checks that it is solveable with out
        requiring the user taking a wild guess.
        """

        def update_neighbour(row: int, column: int):
            """Increment the adjacent_mines count"""
            if row < 0 or column < 0:
                return

            if row >= self.rows or column >= self.columns:
                return

            self.cell(row, column).adjacent_mines += 1

        for _ in range(self.mines):
            # Choose a location for the mine, but keep picking another if it
            # is the starting location or if it already has a mine.
            mine_row, mine_column = row, column
            while (mine_row == row and mine_column == column or
                   self.cell(mine_row, mine_column).has_mine):
                mine_row = random.randint(0, self.rows - 1)
                mine_column = random.randint(0, self.columns - 1)

            self.cell(mine_row, mine_column).has_mine = True

            # Increment the neighbour count.
            for neighbour in self._neighbours_of(mine_row, mine_column):
                neighbour_row, neighbour_column = neighbour
                update_neighbour(neighbour_row, neighbour_column)

    def _neighbours_of(self, row: int, column: int):
        """The absolute coordinates of neighbours for row and column.

        This takes into account if column is the left most or right most
        column.

        Parameters
        ----------
        row
            The row in the grid/field to pick in.
        column
            The column in the grid/field to pick in.

        Yields
        ------
            The absolute (row, column) of the neighbouring cells.
        """

        # A list of the offsets to apply to a cell to find neighbours.
        neighbours_offsets = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        for neighbour_dx, neighbour_dy in neighbours_offsets:
            neighbour_row = row + neighbour_dx
            neighbour_column = column + neighbour_dy

            if neighbour_row < 0 or neighbour_column < 0:
                continue

            if neighbour_row >= self.rows or neighbour_column >= self.columns:
                continue

            yield (neighbour_row, neighbour_column)

    def _clear_mines(self, row: int, column: int):
        """Clear the cell at (row, column) and around it.

        Return
        ------
            The cell at (row, column)

        Raises
        ------
        GameOver
            If there was a mine at the location picked.
        """
        cell = self.cell(row, column)
        if cell.flag_state is FlagState.OPEN:
            return cell  # Already opened (cleared), nothing to do.

        if cell.flag_state is FlagState.FLAG:
            # A flag are by-design suppose to be safe from accidentally
            # setting off a mine. The maybes however are not and clicking on
            # a maybe can open it.
            return cell

        if cell.has_mine:
            raise GameOver()

        cell.flag_state = FlagState.OPEN

        # Clear any neighbouring cells if there are no mines next to this one,
        # unless there is a flag in the neighbouring cell.
        #
        # The implementation of Minesweeper that was included with Microsoft
        # Windows, won't remove flags if the user placed. However it will
        # remove maybes (question marks).
        if cell.adjacent_mines == 0:
            for neighbour in self._neighbours_of(row, column):
                neighbour_row, neighbour_column = neighbour
                cell = self.cell(row, column)
                if cell.flag_state == FlagState.FLAG:
                    continue

                # The following will check (row, column) if it has no mines
                # nearby but the check above to see if its already clear will
                # stop it getting going back and forth. As we are a neighbour
                # of our neighbour.
                self._clear_mines(neighbour_row, neighbour_column)
        return cell


def beginner():
    """Return a mine field for beginner players."""
    return MineField(rows=9, columns=9, mines=10)


def intermediate():
    """Return a mine field for intermediate players."""
    return MineField(rows=16, columns=16, mines=40)


def advanced():
    """Return a mine field for advanced players."""
    return MineField(rows=16, columns=30, mines=99)


def print_field(mine_field):
    """Print out a representation of the field to standard out."""
    for row in grouper(mine_field.cells, mine_field.columns):
        print(','.join(str(cell) for cell in row))


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks

    Example
        grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"

    Source
        https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    args = [iter(iterable)] * n
    return itertools.zip_longest(fillvalue=fillvalue, *args)


if __name__ == '__main__':
    field = MineField(rows=5, columns=5, mines=5)
    assert len(field.cells) == 25
    field.pick(0, 0)

    first_mine_at = next(i for i, cell in enumerate(field.cells)
                         if cell.has_mine)
    # This will be a loss
    # field.pick(first_mine_at // field.columns, first_mine_at % field.columns)

    print_field(field)
