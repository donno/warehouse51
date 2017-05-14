"""Provides a usage of a game engine for a breakout clone with PyGame."""
import engine

import pygame
import pygame.locals

class PyGameEngine(engine.Engine):
    """Implemnets a frontend for the Breakout engine using pygame."""

    def __init__(self, display):
        self.display = display
        super(PyGameEngine, self).__init__()

    def update(self):
        """Update the display to show the invaders and player."""

        # Fill the screen with black.
        self.display.fill((0, 0, 0))

        vader_x, vader_y = self.Bounds[:2]

        # Draw the living invaders.
        for row, row_colour in enumerate(self.RowColours):
            for column in range(0, self.BlocksAcrossCount):
                index = row * self.BlocksAcrossCount + column
                if not self.blocks[index]:
                    continue

                padding = self.BlockPadding
                draw_at_x = vader_x + self.BlockWidth * column + padding
                draw_at_y = vader_y + self.BlockHeight * row + padding
                pygame.draw.rect(
                    self.display,
                    row_colour,
                    (draw_at_x,
                     draw_at_y,
                     self.BlockWidth - padding * 2,
                     self.BlockHeight - padding * 2))

        # Draw the player.
        player_x, player_y = self.player_position
        player_x = player_x - self.PlayerWidth // 2
        pygame.draw.rect(self.display,
                         (255, 255, 255),
                         (player_x, player_y, self.PlayerWidth, self.PlayerHeight))

        # Draw the ball
        pygame.draw.circle(self.display, (255, 255, 255), self.ball.position, self.ball.radius)


def main():
    pygame.init()

    display = pygame.display.set_mode((800, 600), 0, 32)
    engine = PyGameEngine(display)

    pygame.display.set_caption(engine.Name)

    count = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.locals.K_LEFT:
                    engine.direction(left=True, pressed=True)
                if event.key == pygame.locals.K_RIGHT:
                    engine.direction(right=True, pressed=True)
            if event.type == pygame.KEYUP:
                if event.key == pygame.locals.K_LEFT:
                    engine.direction(left=True, pressed=False)
                if event.key == pygame.locals.K_RIGHT:
                    engine.direction(right=True, pressed=False)
                if event.key == pygame.locals.K_r:
                    engine.restart()
                    count = 0

        if count == 40 and not engine.is_game_over:
            engine.tick()
            count = -1
        count += 1

        pygame.display.update()


if __name__ == '__main__':
    main()
