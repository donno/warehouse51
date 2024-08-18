"""Parts that represent refer to real parts.

If this module gets large it may be converted to a package with a module
per-vendor.

The author of this module does not provide its accuracy or completeness to the
purchasable components that they represent.

Notes
-----

For Texas Instruments, the device naming is as follows:
  [ Standard Prefix ] [Temperature Range] [Family] [Special Features*]
Where *is Optional so can be blank.

Temperature range:
- 64 - Military
- 74 - Commerical

Family
* LS - Low-Power Schottky Logic
* HS - High-Speed CMOS


A useful page which lists the commonly available NOR Logic Gate IC is:
  https://www.electricaltechnology.org/2018/04/digital-logic-nor-gate.html
  It covers Quad 2 input Nor, Dual 4 input, etc.
"""

import itertools
import unittest

from digital import Input, NotGate, AndGate, NorGate, OrGate


def four_way_nor(a, b, c, d):
    """Return nested gates that represent a 4-input NOR gate."""
    # This first attempt isn't correct where it tried to followed the data
    # sheet of CD74HC4002  based on Figure 7-2. Logic Symbol.
    # not_ab = NandGate(a, b)
    # not_cd = NandGate(c, d)
    # return NotGate(NorGate(not_ab, not_cd))
    a_nor_b = NorGate(a, b)
    c_nor_d = NorGate(c, d)
    return NorGate(
        NorGate(a_nor_b, a_nor_b),
        NorGate(c_nor_d, c_nor_d),
    )


class FourWayNor:
    """Represents a 4 way NOR Gate.

    This would be similar to a CD74HC4002 however it only has one gate instead
    of two.

    CD74HC4002: https://www.ti.com/product/CD74HC4002
    Data sheet:https://www.ti.com/lit/gpn/cd74hc4002
    """

    def __init__(self, a=None, b=None, c=None, d=None):

        self.a = a or Input("a")
        self.b = b or Input("b")
        self.c = c or Input("c")
        self.d = d or Input("d")
        self.output = four_way_nor(self.a, self.b, self.c, self.d)

    def __call__(self, a, b, c, d):
        self.a.set(a)
        self.b.set(b)
        self.c.set(c)
        self.d.set(d)
        return self.output.output


class SN74S260Single:
    """Represents a 5-input NOR Gate.

    The difference between this and a physical SN74S260 is it has two (dual)
    gates.

    SN74S260: https://www.ti.com/product/SN74S260
    Data sheet:https://www.ti.com/lit/gpn/sn74s260

    The boolean function for this is
    Y = (A + B + C + D)'
    """

    def __init__(self, a, b, c, d, e):

        # The following is based on Figure 7-2. Logic Symbol from the data
        # sheet of CD74HC4002.
        a_b = OrGate(a, b)
        c_d_e = OrGate(OrGate(c, d), e)
        self.output = NotGate(OrGate(a_b, c_d_e))


class SN54LS147:
    """10-line Decimal to 4-Line BCD.

    If all inputs are high (lets say True) then all outputs are True. This
    means it produces the opposite to what this is expecting.

    Other versions are:
    - Catalog  : SN74LS147 (https://www.ti.com/product/SN74LS147)
    - Military : SN54LS147 (https://www.ti.com/product/SN54LS147)

    Data sheet:  https://www.ti.com/lit/gpn/sn74ls148

    D = NOR(8', 9')
    """

    def __init__(self, inputs: list[Input | None] = []):
        if len(inputs) == 0:
            inputs = [Input(f"i{i + 1}") for i in range(9)]
        if len(inputs) != 9:
            raise ValueError("There should be 9 inputs")

        self.inputs = inputs[:]

        # The convention I use when converting the logic diagrams from
        # the data sheets is to consider them as columns.

        # Ignore first column.
        # Second column is Inverters with one NOR().
        # Third column is ANDs
        # Fourth column is NORs.

        # To represent the inputs be activate on High-level invert it.
        input_1 = NotGate(self.inputs[0])
        input_2 = NotGate(self.inputs[1])
        input_3 = NotGate(self.inputs[2])
        input_4 = NotGate(self.inputs[3])
        input_5 = NotGate(self.inputs[4])
        input_6 = NotGate(self.inputs[5])
        input_7 = NotGate(self.inputs[6])
        input_8 = NotGate(self.inputs[7])
        input_9 = NotGate(self.inputs[8])

        # Second column
        not_input_2 = NotGate(input_2)
        not_input_4 = NotGate(input_4)
        not_input_5 = NotGate(input_5)
        not_input_6 = NotGate(input_6)
        nor_input_8_9 = NorGate(input_8, input_9)

        # Third column - group A (for output A).
        and_1 = AndGate(
            AndGate(input_1, not_input_2), AndGate(not_input_4, nor_input_8_9)
        )
        and_2 = AndGate(
            AndGate(input_3, not_input_4), AndGate(not_input_6, nor_input_8_9)
        )
        and_3 = AndGate(AndGate(input_5, not_input_6), nor_input_8_9)
        and_4 = AndGate(input_7, nor_input_8_9)
        and_5 = input_9

        # Third column - group B (for output B).
        and_6 = AndGate(
            AndGate(input_2, not_input_4),
            AndGate(not_input_5, nor_input_8_9),
        )
        and_7 = AndGate(
            AndGate(input_3, not_input_4),
            AndGate(not_input_5, nor_input_8_9),
        )
        and_8 = AndGate(input_6, nor_input_8_9)
        and_9 = AndGate(input_7, nor_input_8_9)

        # Third column - group C (for output C)
        and_10 = AndGate(input_4, nor_input_8_9)
        and_11 = AndGate(input_5, nor_input_8_9)
        and_12 = AndGate(input_6, nor_input_8_9)
        and_13 = AndGate(input_7, nor_input_8_9)

        # Fourth column
        self.output_a = SN74S260Single(and_1, and_2, and_3, and_4, and_5)
        self.output_b = FourWayNor(and_6, and_7, and_8, and_9)
        self.output_c = FourWayNor(and_10, and_11, and_12, and_13)
        self.output_d = NorGate(input_8, input_9)

    def __call__(self, *values):
        """Returns which of the 7 segments should be on."""
        for input, value in zip(self.inputs, values):
            input.set(value)

        return [o.output if o else None for o in self.outputs.values()]

    @property
    def outputs(self):
        return {
            "A": self.output_a.output,
            "B": self.output_b.output,
            "C": self.output_c.output,
            "D": self.output_d,
        }


class FourWayNorTests(unittest.TestCase):
    """Simple reminder is output is True only if all inputs are False."""

    def test_0000(self):
        gate = FourWayNor()
        output = gate(False, False, False, False)
        self.assertTrue(output)

    def test_rest(self):
        for input in itertools.product([True, False], repeat=4):
            if not any(input):
                continue  # handled by test_0000.

            with self.subTest(input=input):
                gate = FourWayNor()
                output = gate(*input)
                self.assertEqual(output, False)


class SN54LS147Tests(unittest.TestCase):
    """Tests the SN54LS147 part."""

    def test_zero(self):
        """The decimal zero condition requires all nine data lines to be high.

        This essentially means all True in this case.
        """
        inputs = [True] * 9
        gate = SN54LS147()
        output = gate(*inputs)
        self.assertSequenceEqual(output, [True, True, True, True])

    def test_all_digits(self):
        # For decimal digit 0 to 9.
        expected_values = [
            # A, B, C, D
            [True, True, True, True],  # 0
            [False, True, True, True],  # 1
            [True, False, True, True],  # 2
            [False, False, True, True],  # 3
            [True, True, False, True],  # 4
            [False, True, False, True],  # 5
        ]

        # 9 means the input 9 is low (False)
        # 8 means the input 8 is low (False), and input 9 is high (True).

        for i, expected in zip(range(10), expected_values):
            # Otherwise this is (i << 1) if you want binary.
            bits = [True] * 9
            if i > 0:
                bits[i - 1] = False

            # This is expecting the 8421 encoding.
            with self.subTest(i=i, inputs=bits):
                gate = SN54LS147()
                output = gate(*bits)
                self.assertSequenceEqual(output, expected)

    def test_too_few_inputs(self):
        """Test providing the too few inputs."""
        with self.assertRaises(ValueError):
            SN54LS147([Input("i1"), Input("i2")])

    def test_too_many_inputs(self):
        """Test providing the too many inputs."""
        with self.assertRaises(ValueError):
            inputs = [Input(f"i{i + 1}") for i in range(20)]
            SN54LS147(inputs)
