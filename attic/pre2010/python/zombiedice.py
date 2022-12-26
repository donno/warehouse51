

from itertools import repeat, izip

import random


class Engine:
  Name = "Zombie Dice"

  Dice = {
    'Green': ['brain', 'brain', 'brain', 'shotgun', 'runner', 'runner'],
    'Yellow': ['brain', 'brain', 'brain', 'shotgun', 'runner', 'runner'],
    'Red': ['shotgun', 'shotgun', 'shotgun', 'brain', 'runner', 'runner'],
    }

  def __init__(self, players):
    """Constructs a new Engine for playing Zombie Dice.

    @param players: The number of players.
    @type int
    """

    # Perform an inital shuffle on all the dice.
    for die in self.Dice.itervalues():
      random.shuffle(die)

    #:TODO Disable the ability to set players.

    self.players = players
    self.current_player = 0
    self.current_hand = []

    # Initalise the list of scores for each player.
    self.scores = list(repeat(0, self.players))

  def _count_item(self, item):
    """Returns the number of the provided item in the current players hand"""
    item_count = 0
    for dice, value in self.current_hand:
      if value == item:
        item_count = item_count + 1
    return item_count

  def next_player(self):
    self.current_player = (self.current_player + 1) % self.players
    self.current_hand = []
    return self.current_player

  def alive(self):
    """Returns True if the current player is dead"""

    lives = 3 - self._count_item('shotgun')
    return lives > 0

  def roll(self):
    def _isRunner(dice, value):
      return value == 'runner'

    # Select 3 dice to then roll.
    #
    # If any of the dice in the hand are runners that dice should be re-used
    # instead of picking a new dice and the runners should be removed from the
    # hand.
    dicesPicked = []
    for dice, value in self.current_hand:
      if value == 'runner':
        dicesPicked.append(dice)

    # Update the hand to exclude the runners
    self.current_hand = [
      item for item in self.current_hand if not _isRunner(*item)
      ]

    while len(dicesPicked) < 3:
      dicesPicked.append(random.choice(self.Dice.keys()))

    # Now roll each of the three dice.

    def _roll(name):
      """Rolls a given dice by name"""
      return random.choice(self.Dice[name])

    # For each dice roll one.
    valuesRolled = [ _roll(name) for name in dicesPicked ]

    # Place the rolls into the current players hand.
    self.current_hand.extend( izip(dicesPicked, valuesRolled) )

    return izip(dicesPicked, valuesRolled)

  def out(self):
    # Count the number of brains in the hand and update the score for the
    # current player.
    self.scores[self.current_player] +=  self._count_item('brain')

    # Change the player.
    self.next_player()

class ConsoleFrontend:
  def __init__(self):
    players = raw_input('> Enter the number of players: ')
    players = int(players)

    self.engine = Engine(players)

  def turn(self):
    print ''
    action = ''
    while action not in ['r', 'o', 'h', 's']:
      action = raw_input('> Players %d turn: roll, out, hand or score: [r/o/h/s] ' %
        self.engine.current_player).lower()

    if action == 'r':
      result = self.engine.roll()

      for dice, roll in result:
        print dice, roll
    elif action == 'o':
      self.engine.out()
      self.turn()
    elif action == 's':
      self.score()
    elif action == 'h':
      hand = ''
      for dice, item in self.engine.current_hand:
        hand += item + ' (' + dice + '), '

      if hand:
        print '  Player %d has %s' % (self.engine.current_player, hand)
      else:
        print '  Player %d has no dice' % self.engine.current_player


    if not self.engine.alive():
      print 'Player %d has died' % self.engine.current_player
      self.engine.next_player()

  def score(self):
    print '=' * 79
    print 'SCORES'
    for player, score in enumerate(self.engine.scores):
      print '  Player %d: %d' % (player, score)
    print '=' * 79

  def start(self):
    print 'Starting a game of %s with %d players' % (
      self.engine.Name, self.engine.players)

    while 1: self.turn()

if __name__ == '__main__':
  frontend = ConsoleFrontend()

  frontend.start()