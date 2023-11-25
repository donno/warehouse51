"""Numerical sequences.
"""

import itertools
import math
import unittest


__author__ = "Sean Donnellan"
__copyright__ = "Waived - See __licence__."
__version__ = "0.1.0"
__licence__ = """Sequences in Python by Sean Donnellan is marked with CC0 1.0
Universal. To view a copy of this license, visit
http://creativecommons.org/publicdomain/zero/1.0
"""


def generate_sequence_a000045():
    """Generate the numerical sequence A000045 (Fibonacci numbers).

    F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1.
    """

    previous = 0 # f(0)
    yield previous
    current = 1 # f(1)
    while True:
        yield current
        previous, current = current, current + previous


def value_a140106(n: int):
    """Return the n-th value in the numerical sequence A140106.

    This uses 1-based indexing so n = 1 is the first number in the sequence not
    n = 0.

    See https://oeis.org/A140106/list

    Formula provided by Washington Bomfim, Feb 12 2011.
    """
    if n > 1:
        return math.floor((n - 2) / 2)
    else:
        return 0


def generate_sequence_a140106(starting_n: int = 1):
    """Generate the numerical sequence A140106.

    starting_n uses 1-based indexing so 1 is the first number in the sequence.

    Number of non-congruent diagonals in a regular n-gon.

    The following is the start of the sequence:
    0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11,
    11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 20,
    21, 21, 22, 22, 23, 23, 24, 24, 25, 25, 26, 26, 27, 27, 28, 28, 29, 29, 30,
    30, 31, 31, 32, 32, 33, 33, 34, 34, 35, 35, 36, 36, 37, ...

    Formulas for computing the n-th value in the sequence:
    Option 1) a(n) = floor((n-2)/2), for n > 1, otherwise 0
    Option 2) a(n) = x^4/(1-x-x^2+x^3)
    """
    if starting_n < 2:
        yield 0
        yield 0

    start = value_a140106(starting_n) + 1

    for value in itertools.count(start=start):
        yield value - 1
        yield value


class SequenceA140106Tests(unittest.TestCase):
    def test_value_a140106(self):
        # Compare with the list here: https://oeis.org/A140106/list
        self.assertEqual(value_a140106(1), 0)
        self.assertEqual(value_a140106(2), 0)
        self.assertEqual(value_a140106(3), 0)
        self.assertEqual(value_a140106(4), 1)
        self.assertEqual(value_a140106(5), 1)
        self.assertEqual(value_a140106(6), 2)
        self.assertEqual(value_a140106(7), 2)

        # Try larger numbers.
        self.assertEqual(value_a140106(70), 34)
        self.assertEqual(value_a140106(71), 34)
        self.assertEqual(value_a140106(72), 35)
        self.assertEqual(value_a140106(73), 35)

    def test_generate_sequence_a000045(self):
        sequence = generate_sequence_a000045()
        self.assertEqual(next(sequence), 0)
        self.assertEqual(next(sequence), 1)
        self.assertEqual(next(sequence), 1)
        self.assertEqual(next(sequence), 2)
        self.assertEqual(next(sequence), 3)
        self.assertEqual(next(sequence), 5)
        self.assertEqual(next(sequence), 8)


class SequenceA000045Tests(unittest.TestCase):
    def test_generate_sequence_a000045_alternate_check(self):
        sequence = generate_sequence_a000045()

        fib_0 = next(sequence)
        fib_1 = next(sequence)
        fib_2 = next(sequence)
        fib_3 = next(sequence)
        fib_4 = next(sequence)

        # As per the definition of what fib(0) and fib(1) are gives this:
        self.assertEqual(fib_0, 0)
        self.assertEqual(fib_1, 1)

        # Now check the rest match the formula of fib(n) = fib(n-1) + fib(n-2).
        self.assertEqual(fib_4, fib_3 + fib_2)
        self.assertEqual(fib_3, fib_2 + fib_1)
        self.assertEqual(fib_2, fib_1 + fib_0)

    def test_generate_sequence_a140106(self):
        sequence = generate_sequence_a140106()
        self.assertEqual(next(sequence), 0)
        self.assertEqual(next(sequence), 0)

        self.assertEqual(next(sequence), 0)
        self.assertEqual(next(sequence), 1)

        self.assertEqual(next(sequence), 1)
        self.assertEqual(next(sequence), 2)

        self.assertEqual(next(sequence), 2)
        self.assertEqual(next(sequence), 3)

        self.assertEqual(next(sequence), 3)
        self.assertEqual(next(sequence), 4)


    def test_generate_sequence_a140106_with_start_1(self):
        sequence = generate_sequence_a140106()
        sequence_0 = next(sequence)
        sequence_1 = next(sequence)
        sequence_2 = next(sequence)
        sequence_3 = next(sequence)

        self.assertEqual(sequence_0, 0)
        self.assertEqual(sequence_1, 0)
        self.assertEqual(sequence_2, 0)
        self.assertEqual(sequence_3, 1)

        # The sequence starts at 1 (i.e. it uses 1-based indexing).
        sequence = generate_sequence_a140106(starting_n=1)
        self.assertEqual(next(sequence), sequence_0)
        self.assertEqual(next(sequence), sequence_1)
        self.assertEqual(next(sequence), sequence_2)

    def test_generate_sequence_a140106_with_start_2(self):
        sequence = generate_sequence_a140106()
        sequence_0 = next(sequence)
        sequence_1 = next(sequence)
        sequence_2 = next(sequence)
        sequence_3 = next(sequence)

        self.assertEqual(sequence_0, 0)
        self.assertEqual(sequence_1, 0)
        self.assertEqual(sequence_2, 0)
        self.assertEqual(sequence_3, 1)

        # The sequence starts at 1 (i.e. it uses 1-based indexing).
        sequence = generate_sequence_a140106(starting_n=1)
        self.assertEqual(next(sequence), sequence_0)
        self.assertEqual(next(sequence), sequence_1)
        self.assertEqual(next(sequence), sequence_2)

    def test_generate_sequence_a140106_with_start_odd(self):
        sequence = generate_sequence_a140106()
        sequence_0 = next(sequence)
        sequence_1 = next(sequence)
        sequence_2 = next(sequence)
        sequence_3 = next(sequence)
        sequence_4 = next(sequence)
        sequence_5 = next(sequence)
        sequence_6 = next(sequence)
        sequence_7 = next(sequence)

        self.assertEqual(sequence_0, 0)
        self.assertEqual(sequence_1, 0)

        # The sequence starts at 1 (i.e. it uses 1-based indexing).
        sequence = generate_sequence_a140106(starting_n=3)
        self.assertEqual(next(sequence), sequence_2)
        self.assertEqual(next(sequence), sequence_3)
        self.assertEqual(next(sequence), sequence_4)
        self.assertEqual(next(sequence), sequence_5)
        self.assertEqual(next(sequence), sequence_6)
        self.assertEqual(next(sequence), sequence_7)

def test_generate_sequence_a140106_with_start_odd(self):
        sequence = generate_sequence_a140106()
        sequence_0 = next(sequence)
        sequence_1 = next(sequence)
        sequence_2 = next(sequence)
        sequence_3 = next(sequence)
        sequence_4 = next(sequence)
        sequence_5 = next(sequence)
        sequence_6 = next(sequence)
        sequence_7 = next(sequence)

        self.assertEqual(sequence_0, 0)
        self.assertEqual(sequence_1, 0)
        self.assertEqual(sequence_2, 0)

        # The sequence starts at 1 (i.e. it uses 1-based indexing).
        sequence = generate_sequence_a140106(starting_n=4)
        self.assertEqual(next(sequence), sequence_3)
        self.assertEqual(next(sequence), sequence_4)
        self.assertEqual(next(sequence), sequence_5)
        self.assertEqual(next(sequence), sequence_6)
        self.assertEqual(next(sequence), sequence_7)


if __name__ == '__main__':
    unittest.main()
