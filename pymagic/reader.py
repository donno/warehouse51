"""Reads a card list in Donno's format."""

# TODO: Add a defintion of the grammar and maybe more examples.
# For now see the README.md for an example.
GRAMMAR = """
file: line*

set_list = set_code [comment] \n

<comment> ::= # <any printable character>
<card> ::= \d\d\d[:F|P] [<comment>]
<card-or_comment> :: <card> | <comment>

<set> :: <char> <char> <char> \n <card-or-comment> \n +

line: comment | set |
"""

import unittest

class Comment:
    """Represents a comment left in the file.

    Leading and trailing white-space is considered insignificant and is
    removed.
    """
    def __init__(self, remark):
        self.remark = remark

    def __str__(self):
        return self.remark

    def __repr__(self):
        return "# " + self.remark

class Set:
    """Represents the start of a card list which all belong to this set."""
    def __init__(self, code):
        self.code = code

class Card:
    """Represents a card in a specific set."""
    def __init__(self, set_code, number, kind, count=1):
        self.set_code = set_code
        self.number = number
        self.kind = kind
        self.count = count

    def __str__(self):
        if self.kind:
            return '%03d:%s' % (self.number, self.kind)
        else:
            return '%03d' % self.number

def _line_generator(input_string):
    """Produces a generator for lines in the given input string."""
    previous_new_line = -1
    while True:
      next_new_line = input_string.find('\n', previous_new_line + 1)
      if next_new_line < 0:
          if len(input_string) - previous_new_line > 0:
              yield input_string[previous_new_line + 1:]
          break
      yield input_string[previous_new_line + 1:next_new_line]
      previous_new_line = next_new_line

def parse_string(input_string, expand=True):
    """
    expand: Expand out duplicates (multiples) so the resulting sequence
            contains the duplicates. Otherwise each item will contain the
            number of duplicates instead.
    """
    for token in parse_lines(_line_generator(input_string), expand):
        yield token

def parse_lines(lines, expand):
    """
    lines: must be a sequence of strings that represents lines in a card list.
    expand: Expand out duplicates (multiples) so the resulting sequence
            contains the duplicates. Otherwise each item will contain the
            number of duplicates instead.
    """
    current_set = None

    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if line.startswith('#'):
            yield Comment(line[1:].strip())
        elif not current_set and line:
            current_set, _, comment = line.partition('#')
            current_set = Set(current_set.strip())

            yield current_set

            if comment:
                yield Comment(comment.strip())
        elif line.startswith('==='):
            # This should appear after a set before the card list.
            # It just helps separate the code from the numbers.
            #
            # This isn't strictly required.
            pass
        elif line:
                code, _, comment = line.partition('#')
                code, _, multiplier = code.partition('*')
                code, _, kind = code.partition(':')
                multiplier = int(multiplier.strip() or '1')
                comment = comment.strip()

                # Support split cards.
                split_card = code.strip().endswith('a')
                if split_card:
                    code = code[:code.find('a')]

                if expand:
                    for _ in range(multiplier):
                        try:
                            yield Card(current_set.code, int(code), kind)
                        except ValueError as e:
                            assert len(e.args) == 1
                            e.args = (e.args[0] + ' on line %d' % line_number,)
                            raise
                        if comment:
                            yield Comment(comment)
                else:
                    try:
                        yield Card(current_set.code, int(code), kind, count=multiplier)
                    except ValueError as e:
                        assert len(e.args) == 1
                        e.args = (e.args[0] + ' on line %d' % line_number,)
                        raise
                    if comment:
                        yield Comment(comment)
        else:
            # A blank line marks the end of a set.
            current_set = None


class TestParser(unittest.TestCase):
    def test_comment(self):
        comment = next(parse_string("# Hello"))
        self.assertEqual(comment.remark, "Hello")
        self.assertEqual(str(comment), "Hello")
        self.assertEqual(repr(comment), "# Hello")

    def test_double_comment(self):
        parser = parse_string("# Hello\n# World")

        comment = next(parser)
        self.assertEqual(comment.remark, "Hello")

        comment = next(parser)
        self.assertEqual(comment.remark, "World")

    def test_comment_lose_spaces(self):
        comment = next(parse_string("#     Hello     "))
        self.assertEqual(comment.remark, "Hello")
        self.assertEqual(str(comment), "Hello")
        self.assertEqual(repr(comment), "# Hello")

    def test_single_set_single_card(self):
        card_list = "GRN\n===\n084\n"
        parser = parse_string(card_list)
        current_set = next(parser)
        card = next(parser)

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(card.number, 84)
        self.assertEqual(str(card), '084')
        self.assertRaises(StopIteration, lambda: next(parser))

    def test_single_set_single_card_promo(self):
        card_list = "GRN\n===\n084:P\n"
        parser = parse_string(card_list)
        current_set = next(parser)
        card = next(parser)

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(card.number, 84)
        self.assertEqual(card.kind, 'P')
        self.assertEqual(str(card), '084:P')
        self.assertRaises(StopIteration, lambda: next(parser))

    def test_single_set_single_card_foil(self):
        card_list = "GRN\n===\n084:F\n"
        parser = parse_string(card_list)
        current_set = next(parser)
        card = next(parser)

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(card.number, 84)
        self.assertEqual(card.kind, 'F')
        self.assertEqual(str(card), '084:F')
        self.assertRaises(StopIteration, lambda: next(parser))

    def test_single_set_single_card_with_comments(self):
        card_list = "GRN # From pre-release\n===\n084\n"
        parser = parse_string(card_list)
        current_set = next(parser)
        comment_for_set = next(parser)
        card = next(parser)

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(comment_for_set.remark, "From pre-release")
        self.assertEqual(card.number, 84)
        self.assertRaises(StopIteration, lambda: next(parser))

    def test_single_set_list(self):
        single_set = """GRN
===
001
004
004
"""
        parser = parse_string(single_set)

        current_set = next(parser)
        first_card = next(parser)
        second_card = next(parser)
        third_card = next(parser)

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(first_card.number, 1)
        self.assertEqual(second_card.number, 4)
        self.assertEqual(third_card.number, 4)

        self.assertRaises(StopIteration, lambda: next(parser))

    def test_single_set_duplicates_of_single_card(self):
        card_list = "GRN\n===\n082 * 4\n"
        parser = parse_string(card_list)
        current_set = next(parser)
        cards = [card for card in parser]
        self.assertRaises(StopIteration, lambda: next(parser))

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(len(cards), 4)
        self.assertEqual(cards[0].number, 82)
        self.assertEqual(cards[1].number, 82)
        self.assertEqual(cards[2].number, 82)
        self.assertEqual(cards[3].number, 82)


    def test_single_set_duplicates_of_single_card_non_expand(self):
        card_list = "GRN\n===\n083 * 4\n"

        # Don't expand out multiples in multiple instances of the same card.
        parser = parse_string(card_list, expand=False)
        current_set = next(parser)
        cards = [card for card in parser]
        self.assertRaises(StopIteration, lambda: next(parser))

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].number, 83)
        self.assertEqual(cards[0].count, 4)

    def test_single_set_duplicates_of_few_cards_non_expand(self):
        card_list = "GRN\n===\n083 * 4\n084 * 3\n085 * 8"

        # Don't expand out multiples in multiple instances of the same card.
        parser = parse_string(card_list, expand=False)
        current_set = next(parser)
        cards = [card for card in parser]
        self.assertRaises(StopIteration, lambda: next(parser))

        self.assertEqual(current_set.code, "GRN")
        self.assertEqual(len(cards), 3)
        self.assertEqual(cards[0].number, 83)
        self.assertEqual(cards[0].count, 4)

        self.assertEqual(cards[1].number, 84)
        self.assertEqual(cards[1].count, 3)

        self.assertEqual(cards[2].number, 85)
        self.assertEqual(cards[2].count, 8)

if __name__ == '__main__':
    unittest.main()
