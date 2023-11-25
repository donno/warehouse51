"""Numerical sequences.
"""

import itertools
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


def generate_sequence_a140106(starting_n: int = 0):
    """Generate the numerical sequence A140106.

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
    if starting_n:
        raise NotImplementedError("Starting a given n is not yet implemented.")

    yield 0
    yield 0
    for value in itertools.count(start=1):
        yield value - 1
        yield value


class Tests(unittest.TestCase):
    def test_generate_sequence_a000045(self):
        sequence = generate_sequence_a000045()
        self.assertEqual(next(sequence), 0)
        self.assertEqual(next(sequence), 1)
        self.assertEqual(next(sequence), 1)
        self.assertEqual(next(sequence), 2)
        self.assertEqual(next(sequence), 3)
        self.assertEqual(next(sequence), 5)
        self.assertEqual(next(sequence), 8)

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


if __name__ == '__main__':
    unittest.main()
