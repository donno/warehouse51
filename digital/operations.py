"""Module for representing the operations of digital electronics."""

import unittest


def and_gate(a, b):
    """Return the result of a AND b.

    Returns True if both inputs are true.
    """
    return bool(a and b)


def or_gate(a, b):
    """Return the result of a OR b.

    Returns True if at least one input is true and False otherwise.
    """
    return bool(a or b)


def not_gate(a):
    """Inverts the input."""
    return not a


def nor(a, b):
    """Return the result of a NOR b."""
    return bool(not (a or b))


def xor(a, b):
    """Return the result of a XOR b."""
    return bool(a ^ b)


def full_adder(a, b, carry_in):
    """Represents the digital circuit known as a full adder.

    Return (sum, carry_out).
    """

    c = xor(a, b)

    sum = xor(c, carry_in)

    d = and_gate(c, carry_in)
    e = and_gate(a, b)
    carry_out = or_gate(d, e)

    return sum, carry_out


def full_adder_only_nor(a, b, carry_in):
    """A full adder using only NOR (a universal logic gate)."""
    c = nor(a, b)

    # Expanded
    # d = nor(a, c)
    # e = nor(b, b)
    # f = nor(d, e)
    #
    # This is the collapsed form where if the output is only used in one gate
    # I don't give it a variable name.
    f = nor(nor(a, c), nor(c, b))

    g = nor(carry_in, f)

    carry_out = nor(c, g)

    sum = nor(nor(f, g), nor(g, carry_in))

    return sum, carry_out


def integer_to_bool_array(integer, bit_length=8):
    """Return a boolean array representing the integer.

    The most signifiant bit will be at index 0.
    """
    return [bool(integer & (1 << (7 - n))) for n in range(bit_length)]


def bool_array_to_integer(bool_array):
    """Returns an integer based on the bits set in the boolean array.

    This expects the most signifiant bit to at index 0 of the array.
    """
    value = 0
    for bit in bool_array:
        value = (value << 1) | bit
    return value


def adder_8bit(a, b):
    """Simulates a digital circuit perform 8-bit addition."""
    if a < 0:
        raise ValueError("'a' must be positive integer.")
    if b < 0:
        raise ValueError("'b' must be positive integer.")
    if a.bit_length() > 8:
        raise ValueError("'a' must be less than 255 (8-bit unsigned integer).")
    if b.bit_length() > 8:
        raise ValueError("'b' must be less than 255 (8-bit unsigned integer).")

    # Convert integer to bits.
    bits_a = integer_to_bool_array(a)
    bits_b = integer_to_bool_array(b)

    carry_in = 0
    bits_sum = []
    for bit_a, bit_b in zip(bits_a, bits_b):
        bit_sum, carry_out = full_adder_only_nor(bit_a, bit_b, carry_in)
        bits_sum.append(bit_sum)
        carry_in = carry_out

    return bool_array_to_integer(bits_sum)


class GateTests(unittest.TestCase):

    def test_not(self):
        """Test the and gate."""
        self.assertEqual(not_gate(False), True)
        self.assertEqual(not_gate(True), False)

    def test_and(self):
        """Test the and gate."""
        self.assertEqual(and_gate(False, False), False)
        self.assertEqual(and_gate(False, True), False)
        self.assertEqual(and_gate(True, False), False)
        self.assertEqual(and_gate(True, True), True)

    def test_or_booleans(self):
        """Test the or gate with booleans (True, False)"""
        self.assertEqual(or_gate(False, False), False)
        self.assertEqual(or_gate(False, True), True)
        self.assertEqual(or_gate(True, False), True)
        self.assertEqual(or_gate(True, True), True)

    def test_or_binary(self):
        """Test the or gate with the numbers 0 and 1."""
        self.assertEqual(or_gate(0, 0), False)
        self.assertEqual(or_gate(0, 1), True)
        self.assertEqual(or_gate(1, 0), True)
        self.assertEqual(or_gate(1, 1), True)

    def test_nor(self):
        """Test the nor gate."""
        self.assertEqual(nor(False, False), True)
        self.assertEqual(nor(False, True), False)
        self.assertEqual(nor(True, False), False)
        self.assertEqual(nor(True, True), False)

    def test_xor(self):
        """Test the xor gate."""
        self.assertEqual(xor(False, False), False)
        self.assertEqual(xor(False, True), True)
        self.assertEqual(xor(True, False), True)
        self.assertEqual(xor(True, True), False)


class ComponentTests(unittest.TestCase):

    FULL_ADDER_TRUTH_TABLE = [
        # ((A, B, Carry-in), (Sum, Carry-out))
        ((0, 0, 0), (0, 0)),
        ((0, 0, 1), (1, 0)),
        ((0, 1, 0), (1, 0)),
        ((0, 1, 1), (0, 1)),
        ((1, 0, 0), (1, 0)),
        ((1, 0, 1), (0, 1)),
        ((1, 1, 0), (0, 1)),
        ((1, 1, 1), (1, 1)),
        ]

    def test_full_adder(self):
        """Test the full adder."""
        for inputs, outputs in self.FULL_ADDER_TRUTH_TABLE:
            a, b, carry_in = inputs
            expected_sum, carry_out = outputs
            with self.subTest(a=a, b=b, carry_in=carry_in):
                actual_sum, actual_carry_out = full_adder(*inputs)
                self.assertEqual(actual_sum, bool(expected_sum))
                self.assertEqual(actual_carry_out, bool(carry_out))

    def test_full_adder_only_nor(self):
        """Test the full adder with only using nor gates."""
        for inputs, outputs in self.FULL_ADDER_TRUTH_TABLE:
            a, b, carry_in = inputs
            expected_sum, carry_out = outputs
            with self.subTest(a=a, b=b, carry_in=carry_in):
                actual_sum, actual_carry_out = full_adder_only_nor(*inputs)

                self.assertEqual(actual_sum, bool(expected_sum))
                self.assertEqual(actual_carry_out, bool(carry_out))

    def test_adder_8bit(self):
        self.assertEqual(adder_8bit(2, 5), 7)

        # Test (0 to N) + 0
        for i in range(256):
            self.assertEqual(adder_8bit(i, 0), i)

        # Test 0 + (0 to N)
        for i in range(256):
            self.assertEqual(adder_8bit(0, i), i)


if __name__ == '__main__':
    unittest.main()
