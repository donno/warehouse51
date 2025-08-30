"""Implement the game of Fizz-Buzz.

This game is typically played by children at school to test their division
skill. They sit in a circle if a player makes a mistake they are eliminated
and the winner is the final player left in.
"""

import itertools
import doctest


def fizzbuzz_traditional():
    """A traditional implementation of Fizz-Buzz game.

    Examples
    --------
    >>> list(itertools.islice(fizzbuzz_traditional(), 6))
    [1, 2, 'Fizz', 4, 'Buzz', 'Fizz']

    >>> list(itertools.islice(fizzbuzz_traditional(), 6, 15))
    [7, 8, 'Fizz', 'Buzz', 11, 'Fizz', 13, 14, 'FizzBuzz']
    """
    for n in itertools.count(1):
        result = "Fizz" if n % 3 == 0 else ""
        if n % 5 == 0:
            result += "Buzz"

        yield result or n


def fizzbuzz_precompute():
    """A implementation using precomputed sequence of Fizz-Buzz game.

    This is because after 15, it repeats back to the start, i.e. 16, 17, 18 are
    the same as 1, 2 and 3..

    Examples
    --------
    >>> list(itertools.islice(fizzbuzz_precompute(), 6))
    [1, 2, 'Fizz', 4, 'Buzz', 'Fizz']

    >>> list(itertools.islice(fizzbuzz_precompute(), 6, 15))
    [7, 8, 'Fizz', 'Buzz', 11, 'Fizz', 13, 14, 'FizzBuzz']

    >>> limited_selection = itertools.islice(fizzbuzz_precompute(), 200)
    >>> all(a == b for a, b in zip(limited_selection, fizzbuzz_traditional()))
    True
    """
    cache = [
        v if isinstance(v, str) else 0
        for v in itertools.islice(fizzbuzz_traditional(), 15)
    ]

    for n, v in zip(itertools.count(1), itertools.cycle(cache)):
        if v:
            yield v
        else:
            yield n


def fizzbuzz(start: int = 1):
    """A implementation of Fizz-Buzz game.

    This is because after 15, it repeats back to the start, i.e. 16, 17, 18 are
    the same as 1, 2 and 3..

    Parameters
    ----------
    start
        The number to start at.
        This is 1-based index.

    Examples
    --------
    >>> list(itertools.islice(fizzbuzz(), 6))
    [1, 2, 'Fizz', 4, 'Buzz', 'Fizz']

    >>> list(itertools.islice(fizzbuzz(), 6, 15))
    [7, 8, 'Fizz', 'Buzz', 11, 'Fizz', 13, 14, 'FizzBuzz']

    >>> list(itertools.islice(fizzbuzz(start=7), 15 - 6))
    [7, 8, 'Fizz', 'Buzz', 11, 'Fizz', 13, 14, 'FizzBuzz']

    >>> list(itertools.islice(fizzbuzz(start=100), 7))
    ['Buzz', 101, 'Fizz', 103, 104, 'FizzBuzz', 106]
    """
    cache = [
        v if isinstance(v, str) else 0
        for v in itertools.islice(fizzbuzz_traditional(), 15)
    ]

    modulus = len(cache)
    for n in itertools.count(start):
        yield cache[(n - 1) % modulus] or n


if __name__ == "__main__":
    doctest.testmod()
