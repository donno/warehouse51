"""Provides a usage of a game engine for a space invader style clone with
PyGame."""
import engine

import pygame
import pygame.locals

__version__ = '0.1.0'
__copyright__ = "Copyright (C) 2017 Sean Donnellan"

GameOver = engine.GameOver


class PyGameEngine(engine.Engine):
    def __init__(self, display):
        self.display = display
        super(PyGameEngine, self).__init__()

    def update(self):
        """Update the display to show the invaders and player."""

        # Fill the screen with black.
        self.display.fill((0, 0, 0))

        vader_x, vader_y = self.invader_position

        # Draw the living invaders.
        for row in range(0, len(self.ScorePerRow)):
            for column in range(0, 11):
                index = row * 11 + column
                if not self.invaders[index]:
                    continue

                padding = 2
                draw_at_x = vader_x + self.InvaderWidth * column + padding
                draw_at_y = vader_y + self.InvaderWidth * row + padding
                pygame.draw.rect(
                    self.display,
                    (255, 0, 0),
                    (draw_at_x,
                     draw_at_y,
                     self.InvaderWidth - padding * 2,
                     self.InvaderWidth - padding * 2))

        # Draw the player.
        player_x, player_y = self.player_position
        player_x = player_x - 100 / 2
        pygame.draw.rect(self.display, (255, 255, 255),
                         (player_x, player_y, 100, 50))

        # Draw the bullet
        if self.player_bullet:
            pygame.draw.rect(self.display, (255, 255, 255),
                             (self.player_bullet.position_x,
                              self.player_bullet.position_y,
                              self.player_bullet.Width,
                              10))


def main():
    pygame.init()

    display = pygame.display.set_mode((720, 576), 0, 32)
    engine = PyGameEngine(display)

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
                if event.key == pygame.locals.K_SPACE:
                    engine.fire()

            if event.type == pygame.KEYUP:
                if event.key == pygame.locals.K_LEFT:
                    engine.direction(left=True, pressed=False)
                if event.key == pygame.locals.K_RIGHT:
                    engine.direction(right=True, pressed=False)

        if count == 20 and not engine.is_game_over:
            try:
                engine.tick()
            except GameOver:
                print('Game over')
            count = -1
        count += 1

        pygame.display.update()


if __name__ == '__main__':
    main()
