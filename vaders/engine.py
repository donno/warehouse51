"""Provides a game engine for a space invader style clone."""

__copyright__ = "Copyright (C) 2017 Sean Donnellan"


class GameOver(Exception):
    """Thrown when the game is over and the player has failed.

    The invaders have reaced the earth.
    """
    pass


class Range(object):
    """Represents a 1D extent also known as a range."""
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __repr__(self):
        return "Range(%d, %d)" % (self.lower, self.upper)

    def contains(self, value):
        """Checks if value is within the range from lower to upper."""
        return value < self.upper and value > self.lower


class Bullet(object):
    """Represents a bullet that the player or enemies can fire at one another.
    """

    Width = 4
    """The width of the bullet."""

    def __init__(self, start_x, start_y, velocity):
        """Construct a bullet with a starting position and velocity.

        Bullets always travel vertically.

        start_y: The top most point of the bullet.
        """
        self.position_x = start_x
        self.position_y = start_y
        self.velocity = velocity

    def tick(self):
        """Updates the position based on the velocity."""
        self.position_y += self.velocity


class Engine(object):
    """Game engine for a space invader style clone."""
    ScorePerRow = [30, 20, 20, 10, 10]

    Bounds = (10, 50, 710, 500)

    InvaderWidth = 36

    def __init__(self):
        self.invader_velocity = -1
        self.invader_position = ()
        self.player_position = (0, 0)
        self.player_bullet = None
        self.player_score = 0
        self.is_game_over = False
        self.restart()

    def restart(self):
        """Restarts the game back to the initial state."""

        # There are 11 invaders per row, so 55 invaders.
        self.invaders = [True for _ in range(0, 11 * len(self.ScorePerRow))]

        # Keep track of the number of invaders that are alive in each column.
        self._invaders_alive_by_column = [
            len(self.ScorePerRow) for _ in range(0, 11)
            ]

        # We only need to track the position of the first left most invader.
        self.invader_position = (100, self.Bounds[1])

        self.invader_velocity = -1

        self.player_velocity = 0
        self.player_position = (100, self.Bounds[3])
        self.player_bullet = None
        self.player_score = 0
        self.is_game_over = False
        self.update()

    def tick(self):
        """Performs one tick of the engine to update the positions."""

        self.invader_position = (
            self.invader_position[0] + self.invader_velocity,
            self.invader_position[1],
            )
        # Check bounds.
        self._check_invaders_are_in_bounds()

        if self.player_bullet:
            self.player_bullet.tick()

            # Check collision between player bullet and invaders.
            if self._check_if_invaders_are_hit():
                # Update the speed of the invaders based on the number of
                # remaining invaders.
                invader_alive_count = self.invaders.count(True)

                if invader_alive_count < 2:
                    new_velocity = 16
                elif invader_alive_count < 9:
                    new_velocity = 12
                elif invader_alive_count < 14:
                    new_velocity = 10
                else:
                    # Some value between 1 and 9 based on the number of vaders
                    # alive.
                    # TODO: Make this of the form:
                    # a * invader_alive_count ** 3 + b * invader_alive_count ** 2 + c * invadersAliveTotal + d
                    new_velocity = 5

                if self.invader_velocity < 0:
                    self.invader_velocity = -new_velocity / 5
                else:
                    self.invader_velocity = new_velocity / 5
            else:
                # Check collision with the top of screen and destory the bullet
                # if it is outsides the bound.
                if self.player_bullet.position_y < self.Bounds[1]:
                    self.player_bullet = None

        # Update the players position
        self.player_position = (
            self.player_position[0] + self.player_velocity,
            self.player_position[1],
            )

        # Prevent the player from going out of bounds.
        if self.player_position[0] < self.Bounds[0]:
            self.player_position = (self.Bounds[0], self.player_position[1])
        if self.player_position[0] > self.Bounds[2]:
            self.player_position = (self.Bounds[2], self.player_position[1])

        self.update()

    def update(self):
        """Override this function."""

    def direction(self, left=False, right=False, pressed=False):
        """Handle a change in the player's direction."""
        if left:
            if pressed:
                self.player_velocity -= 8
            else:
                self.player_velocity += 8
        if right:
            if pressed:
                self.player_velocity += 8
            else:
                self.player_velocity -= 8

    def fire(self):
        """Fire the player's weapon."""
        if not self.player_bullet:
            start_x, start_y = self.player_position
            self.player_bullet = Bullet(start_x, start_y, velocity=-14)

    def _check_invaders_are_in_bounds(self):
        """Checks that the invaders are with in the bounds of the play area.

        If its exceeds the left or the right bounds they reverse direction.
        """

        assert any(self._invaders_alive_by_column), "At least one invader must be alive."

        if self.invader_velocity < 0:
            # The invaders are moving left.

            # Left most alive column of invaders is:
            for column, count in enumerate(self._invaders_alive_by_column):
                if count > 0:
                    break
            else:
                column = None
            alive_column_index = column

            # Find the x of the left most alive column.
            invaders_x = self.invader_position[0] + self.InvaderWidth * alive_column_index

            if invaders_x < self.Bounds[0]:
                self.invader_velocity = self.invader_velocity * -1
        else:
            assert self.invader_velocity > 0, "If not moving left must move right"

            alive_column_index = len(self._invaders_alive_by_column) - \
                next(i for i, b in enumerate(reversed(self._invaders_alive_by_column)) if b)

            # Find the x of the right most alive column.
            invaders_x = self.invader_position[0] + self.InvaderWidth * (alive_column_index + 1)
            if invaders_x > self.Bounds[2]:
                self.invader_velocity = self.invader_velocity * -1
                self.invader_position = (
                    self.invader_position[0],
                    self.invader_position[1] + 18,
                    )

        # Handle the game over (i.e the bottom)
        #
        # Check if any invaders, living or dead is  landed on earth.
        vaders_y_range = Range(self.invader_position[1],
                               self.invader_position[1] +
                               self.InvaderWidth * len(self.ScorePerRow))

        if vaders_y_range.contains(self.Bounds[3]):
            # There is a vader landed on earth.
            # Check if any of the invaders on that row are alive.
            row = (self.Bounds[3] - self.invader_position[1]) / self.InvaderWidth

            start_index = len(self._invaders_alive_by_column) * row
            end_index = start_index + len(self._invaders_alive_by_column)
            vaders_in_row = self.invaders[start_index:end_index]

            # Find if any invader in the row is alive, if so its game over.
            if any(vaders_in_row):
                self.is_game_over = True
                raise GameOver

    def _check_if_invaders_are_hit(self):
        """Check if an invader is hit by the player's bullet.

        If an invader was hit the player's bullet is destoryed the invader is
        killed and the score is updated.
        """
        if not self.player_bullet:
            return

        # First check the bounding box of all invaders, living or dead .
        vaders_y_range = Range(self.invader_position[1],
                               self.invader_position[1] +
                               self.InvaderWidth * len(self.ScorePerRow))

        if not vaders_y_range.contains(self.player_bullet.position_y):
            return

        vaders_x_range = Range(self.invader_position[0],
                               self.invader_position[0] +
                               self.InvaderWidth * len(self._invaders_alive_by_column))

        if not vaders_x_range.contains(self.player_bullet.position_x):
            return

        # Compute the row and column that lies within the line of sight of the invaders.
        column = int((self.player_bullet.position_x - self.invader_position[0]) // self.InvaderWidth)
        row = int((self.player_bullet.position_y - self.invader_position[1]) // self.InvaderWidth)
        invader_index = column + len(self._invaders_alive_by_column) * row

        if self.invaders[invader_index]:
            # Kill the invader and hide the bullets.
            self.invaders[invader_index] = False
            self.player_bullet = None
            self.player_score += self.ScorePerRow[row]
            self._invaders_alive_by_column[column] -= 1
            return True

        return False

def handle_inputs(engine):
    """Handle user input using the https://github.com/zeth/inputs

    This may be helpful if the user interface library you are using doesn't
    provide its own way of accessing the inputs.
    """
    from inputs import get_key

    history = {}
    while True:
        events = get_key()
        for event in events:
            if event.code == 'KEY_LEFT':
                if history.get(event.code, 0) != event.state:
                    engine.direction(left=True, pressed=event.state == 1)
                history[event.code] = event.state
            if event.code == 'KEY_RIGHT':
                if history.get(event.code, 0) != event.state:
                    engine.direction(right=True, pressed=event.state == 1)
                history[event.code] = event.state
            if event.code == 'KEY_SPACE' and event.state == 1:
                if history.get('KEY_SPACE', 0) != event.state:
                    engine.fire()
            if event.code == 'KEY_ESC':
                return True

if __name__ == '__main__':
    ENGINE = Engine()
    ENGINE.fire()
    ENGINE.player_bullet.position_y = ENGINE.invader_position[1] + 40
    ENGINE.player_bullet.position_x += 40
    ENGINE.tick()
