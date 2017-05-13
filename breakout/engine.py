"""Provides a game engine for a breakout style clone."""


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


class Ball(object):
    """Represents a ball that the player uses to deflect into blocks."""

    radius = 6
    """The radius of the ball which is a circle or sphere in 3D."""

    def __init__(self, start_x, start_y):
        """Construct a ball with a starting position."""
        self.position = [start_x, start_y]
        self.velocity = (2, -2)
        self.velocity = (6, -6)

    def tick(self):
        """Updates the position based on the velocity."""
        self.position = [sum(e) for e in zip(self.position, self.velocity)]


class Engine(object):
    """Game engine for a breakout style clone."""

    """The name of the game this engine is for."""
    Name = 'Breakout-like'

    Bounds = (10, 10, 790, 560)

    BlocksAcrossCount = 13

    BlockPadding = 2
    BlockWidth = 60
    BlockHeight = 20

    PlayerWidth = 100
    PlayerHeight = 20

    RowColours = [0xB71C1C, 0xEF6C00, 0xFFEB3B, 0x4CAF50, 0x673AB7, 0x3F51B5]

    def __init__(self):
        self.player_position = (0, 0)
        self.player_score = 0
        self.player_velocity = 0
        self.is_game_over = False

        ball_x = self.Bounds[0] + (self.Bounds[2] - self.Bounds[0]) // 2

        self.ball = Ball(ball_x, self.Bounds[3] - 50)
        self.restart()

    def restart(self):
        """Restarts the game back to the inital state."""

        self.blocks = [True for _ in range(0, self.BlocksAcrossCount * len(self.RowColours))]

        # Keep track of the number of blocks that are alive in each column.
        self._blocks_alive_by_column = [
            len(self.RowColours) for _ in range(0, self.BlocksAcrossCount)
            ]

        self.player_position = (100, self.Bounds[3] - 20)
        self.player_score = 0
        self.player_velocity = 0
        self.is_game_over = False
        self.update()

    def tick(self):
        """Performs one tick of the engine to update the positions."""
        # Update the players position
        #
        # By prevent the player from going out of bounds.
        new_player_x = max(self.Bounds[0] + self.PlayerWidth // 2,
                           self.player_position[0] + self.player_velocity)
        new_player_x = min(self.Bounds[2] - self.PlayerWidth // 2, new_player_x)
        self.player_position = (
            new_player_x,
            self.player_position[1],
            )

        # Update the balls position
        self.ball.tick()

        # Handle collision detection/bouncing off the walls.
        ball_x, ball_y = self.ball.position
        if ball_x + self.ball.radius > self.Bounds[2]:
            self.ball.velocity = (-self.ball.velocity[0], self.ball.velocity[1])
        if ball_y - self.ball.radius < self.Bounds[1]:
            self.ball.velocity = (self.ball.velocity[0], -self.ball.velocity[1])
        if ball_x - self.ball.radius < self.Bounds[0]:
            self.ball.velocity = (-self.ball.velocity[0], self.ball.velocity[1])

        self._handle_ball_hit_block()

        if ball_y > self.player_position[1]:
            player_range = Range(self.player_position[0] - self.PlayerWidth // 2,
                                 self.player_position[0] + self.PlayerWidth // 2)

            if player_range.contains(ball_x):
                # This should probably handle the making angle shots better i.e, take
                # into account the velocity of the player at the point of impact.
                self.ball.velocity = (self.ball.velocity[0], -self.ball.velocity[1])

        if ball_y + self.ball.radius > self.Bounds[3]:
            self.is_game_over = True
            #self.game_over_reason = 'Ball went out of play.'

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

    def _handle_ball_hit_block(self):
        """Checks if the ball has hit a block, if so destory the block. """

        # First check the bounding box of all blocks, living or dead .
        blocks_y_range = Range(self.Bounds[1],
                               self.Bounds[1] + self.BlockHeight * len(self.RowColours))

        if not blocks_y_range.contains(self.ball.position[1]):
            return

        # In practice, the next check sshould always be true as the blocks should span the
        # width of the bounds.
        block_x_range = Range(self.Bounds[0],
                              self.Bounds[1] +
                              self.BlockWidth * len(self._blocks_alive_by_column))

        if not block_x_range.contains(self.ball.position[0]):
            return

        # Compute the row and column that lies within the line of sight of the block.
        column = (self.ball.position[0] - self.Bounds[0]) // (self.BlockWidth + self.BlockPadding)
        row = (self.ball.position[1] - self.Bounds[1]) // (self.BlockHeight + self.BlockPadding)

        block_index = column + len(self._blocks_alive_by_column) * row

        if self.blocks[block_index]:
            # Destory the block.
            self.blocks[block_index] = False
            self.player_score += 20
            self._blocks_alive_by_column[column] -= 1

            # Relfect the ball.
            self.ball.velocity = (self.ball.velocity[0], -self.ball.velocity[1])
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
            if event.code == 'KEY_ESC':
                return True
