"""A very early implementation of Freecell variant called SHENZHEN SOLITAIRE
by Zachtronics.

The playable game that this is based on is Steam:
  https://store.steampowered.com/app/570490/SHENZHEN_SOLITAIRE/
"""

import enum
import unittest

__version__ = '0.2.0'
__copyright__ = "Copyright 2018, https://github.com/donno/"


class Colour(enum.Enum):
    Green = 1
    Red = 2
    Black = 3


class Card(object):
    def __init__(self, face_value, colour):
        self.face_value = face_value
        self.colour = colour

    def __str__(self):
        return 'Card(%s, %s)' % (self.face_value, self.colour)

    def is_numbered_card(self):
        return self.face_value >= 1 and self.face_value <= 10

    def can_stack_on(self, other):
        """Return true if this card can be stacked on top of other."""
        if not self.is_numbered_card():
            return False
        if not other.is_numbered_card():
            return False
        return (self.colour != other.colour and
                self.face_value + 1 == other.face_value)


class RemovedPile(object):
    def __init__(self):
        self.by_colour = dict(
            (colour, 0) for colour in [Colour.Green, Colour.Red, Colour.Black]
            )

    def can_remove_card(self, card):
        """Return true if the card can be removed from placed and placed in
        the removed pile."""
        last_card_for_colour = self.by_colour[card.colour]
        return last_card_for_colour + 1 == card.face_value

    def place_card(self, card):
        assert self.can_remove_card(card)
        if self.can_remove_card(card):
            self.by_colour[card.colour] = card.face_value


class PlayMat(object):
    def __init__(self):
        # This is where numbered cards will be removed from play.
        self.remove_pile = RemovedPile()

        # This is where numbered cards can temporary be removed from play.
        #
        # This is where dragon cards can be removed from play once all
        # four the the same colour appears on the top of a stack.
        # self.holding_area = HoldingArea()

        # The main play area the goal is to remove all cards from here to the
        # remove pile (numbered) or holding area (dragons)
        self.stacks = []

    """
    Ideas:

    - Provide a function that returns a list of the possible actions.
      * move top card from a stack to the remove pile
      * move top card from a stack to the holding area
      * move a ordered stack from one stack to another stack.
      * move four dragon cards from play. Take up a space in the holding area.

    - Define a set of actions that can be constructred and applied.
      Basically these actions would be the same as above.
    """


class TestCard(unittest.TestCase):

    def test_is_numbered_card(self):
        red_five = Card(5, Colour.Red)
        green_five = Card(5, Colour.Green)
        green_six = Card(6, Colour.Green)

        self.assertTrue(red_five.is_numbered_card())
        self.assertTrue(green_five.is_numbered_card())
        self.assertTrue(green_six.is_numbered_card())

    def test_can_stack_on(self):
        red_five = Card(5, Colour.Red)
        green_five = Card(5, Colour.Green)
        green_six = Card(6, Colour.Green)

        self.assertTrue(red_five.can_stack_on(green_six))

        # A green six on a red five of is not allowed because they need to be
        # increasing.
        self.assertFalse(green_six.can_stack_on(red_five))

        # They need to be a different colour
        self.assertFalse(green_five.can_stack_on(green_six))

        # Check the above two conditions together.
        self.assertFalse(green_six.can_stack_on(green_five))

        # Check they can't go on themselves.
        self.assertFalse(red_five.can_stack_on(red_five))


class TestClearPile(unittest.TestCase):
    def test_can_remove_card_start(self):
        green_one = Card(1, Colour.Green)
        green_two = Card(2, Colour.Green)
        green_three = Card(3, Colour.Green)

        remove_pile = RemovedPile()

        # Only the one can be removed to begin with.
        self.assertTrue(remove_pile.can_remove_card(green_one))
        self.assertFalse(remove_pile.can_remove_card(green_two))
        self.assertFalse(remove_pile.can_remove_card(green_three))

    def test_can_remove_card(self):
        green_one = Card(1, Colour.Green)
        green_two = Card(2, Colour.Green)
        green_three = Card(3, Colour.Green)

        remove_pile = RemovedPile()
        remove_pile.place_card(green_one)

        self.assertTrue(remove_pile.can_remove_card(green_two))
        self.assertFalse(remove_pile.can_remove_card(green_three))

        # This should be impossible because there is only single card of each
        # number and colour pair. It could make for a neat extention if there
        # were "multiple decks", like spider solitaire.
        self.assertFalse(remove_pile.can_remove_card(green_one))


if __name__ == '__main__':
    unittest.main()

    cards = []
    for colour in [Colour.Green, Colour.Red, Colour.Black]:
        cards.extend(Card(face_value=value, colour=colour)
                     for value in range(1, 10))
