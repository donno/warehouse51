"""Module for representing digital electronics using classes which enable it
to return representations of the system and thus visit the gates rather than
only evaluate them."""

import io
import unittest

__TODO__ = """
- Try to make use of subgraph in GraphViz to represent component like the
  FullAdder as one unit.
- Improve Visitor to recognise the name of outputs is the name of the output
  of the gate not the gate itself.
- Create a half-adder to start the 8-bit adder instead of using a full-adder
  with the carry set to 0.
- Better testing of the Output class. It was added to be used in graphs and the
  visitor at the moment so evaluation while works is not quite as nice as I
  would like.
"""


class Input:
    """Represents the input of a gate, it has an output which is populated
    when it is set with a value.

    The input can be given a name.
    """

    def __init__(self, name):
        self.name = name
        self.callbacks = []
        self._output = None

    @property
    def output(self):
        """The value of the input, which is output to be consumed by an input.
        """
        return self._output

    @output.setter
    def output(self, value):
        """Set the output of the input, which is like setting its value.

        This will trigger anything depending on this value to be evaluated.
        """

        self._output = value

        for callback in self.callbacks:
            callback.eval()

    def set(self, value):
        """Set the output of the input, which is like setting its value.

        This will trigger anything depending on this value to be evaluated."""
        self.output = value

    def register_with(self, dependant):
        """Register with this input to inform dependant when the value is set.

        It is expected that dependant has an eval() function.
        """
        self.callbacks.append(dependant)

    def __repr__(self) -> str:
        return f'Input({self.name!r})'

    def __str__(self) -> str:
        return self.name


class Output:
    """Represents the output of a component which is an input to another
    component/gate.

    This is used to closely tie the output pin on the given component to
    something else.
    """

    def __init__(self, name, component, output_index):
        self.name = name
        self.component = component

        # The output caches if it was N'th output of the component. This avoids
        # having to go find this output in components.outputs.
        self.output_index = output_index

        self._output = None
        self.callbacks = []

    @property
    def output(self):
        """The value of the input, which is output to be consumed by an input.
        """
        return self._output

    @output.setter
    def output(self, value):
        """Set the output of this output.

        This will trigger anything depending on this value to be evaluated.
        """

        self._output = value

        for callback in self.callbacks:
            callback.eval()

    def set(self, value):
        """Set the value of this output.

        This will trigger anything depending on this value to be evaluated.
        """

        self.output = value

    def register_with(self, dependant):
        """Register with this input to inform dependant when the value is set.

        It is expected that dependant has an eval() function.
        """
        self.callbacks.append(dependant)

    def __repr__(self) -> str:
        return f'Output({self.name})'

    def __str__(self) -> str:
        return self.name


class NotGate:
    """Inverts the given input a.k.a computes !a from a."""
    def __init__(self, a):
        self.a = a
        self.output = None
        self.callbacks = []

        # Register ourself with the input so we are called when the input is
        # provided.
        self.a.register_with(self)

    def register_with(self, dependant):
        """Register with this gate to inform dependant when the output is set.

        It is expected that dependant has an eval() function.
        """
        self.callbacks.append(dependant)

    def eval(self):
        if self.a.output is not None:
            self.output = self(self.a.output)
            for callback in self.callbacks:
                callback.eval()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.a!r})'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.a})'

    def __call__(self, a):
        return not a


class BinaryGate:
    """Binary gate takes two inputs and produces one output."""

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.output = None
        self.callbacks = []

        # Register ourself with the inputs so we are called when the input is
        # provided.
        self.a.register_with(self)
        self.b.register_with(self)

    def register_with(self, dependant):
        """Register with this gate to inform dependant when the output is set.

        It is expected that dependant has an eval() function.
        """
        self.callbacks.append(dependant)

    def eval(self):
        if self.a.output is not None and self.b.output is not None:
            self.output = self(self.a.output, self.b.output)

            for callback in self.callbacks:
                callback.eval()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.a!r}, {self.b!r})'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.a}, {self.b})'

    def __call__(self, a, b):
        raise NotImplementedError('Derived classed must override this.')

    # TODO: Add a reset so all the inputs can be reset.


class AndGate(BinaryGate):
    """And gate has two inputs and one output.

    It returns true only if both inputs are true.
    """

    def __call__(self, a, b):
        return bool(a and b)


class OrGate(BinaryGate):
    """Or gate has two inputs and one output.

    It returns true if at least one input is true.
    """

    def __call__(self, a, b):
        return bool(a or b)


class NorGate(BinaryGate):
    def __call__(self, a, b):
        return bool(not (a or b))


class XorGate(BinaryGate):
    def __call__(self, a, b):
        return bool(a ^ b)


class FullAdder:
    """Represents the digital electronic component known as a full adder.

    It essentially can add two bits together.

    It returns the sum and the carry, the carry is like the overflow.
    """
    def __init__(self, a=None, b=None, carry_in=None):
        # Inputs
        self.a = a or Input('a')
        self.b = b or Input('b')
        self.carry_in = carry_in or Input('carry_in')

        # In between.
        c = XorGate(self.a, self.b)
        d = AndGate(c, self.carry_in)
        e = AndGate(self.a, self.b)

        # Outputs
        self.carry_out = OrGate(d, e)
        self.sum = XorGate(c, self.carry_in)

    def __call__(self, a, b, carry_in):
        """Return (sum, carry_out)"""

        self.a.set(a)
        self.b.set(b)
        self.carry_in.set(carry_in)

        return self.sum.output, self.carry_out.output

    @property
    def outputs(self) -> dict:
        """The outputs of this component."""
        return {
            'sum': self.sum,
            'carry_out': self.carry_out,
        }


class FullAdderNorOnly:
    """A full adder using only NOR (a universal logic gate)."""

    def __init__(self, a=None, b=None, carry_in=None):
        # Inputs
        self.a = a or Input('a')
        self.b = b or Input('b')
        self.carry_in = carry_in or Input('carry_in')

        # In between.
        c = NorGate(self.a, self.b)

        f = NorGate(NorGate(self.a, c), NorGate(c, self.b))
        g = NorGate(self.carry_in, f)

        # Outputs
        self.carry_out = NorGate(c, g)
        self.sum = NorGate(NorGate(f, g), NorGate(g, self.carry_in))

    def __call__(self, a, b, carry_in):
        """Return (sum, carry_out)"""
        self.a.set(a)
        self.b.set(b)
        self.carry_in.set(carry_in)

        return self.sum.output, self.carry_out.output

    @property
    def outputs(self) -> dict:
        """The outputs of this component."""
        return {
            'sum': self.sum,
            'carry_out': self.carry_out,
        }


class FullAdderOrAndNotOnly:
    """A full adder using only or and not.

    This is a deconstruction of a NOR gate."""

    def __init__(self, a=None, b=None, carry_in=None):
        # Inputs
        self.a = a or Input('a')
        self.b = b or Input('b')
        self.carry_in = carry_in or Input('carry_in')

        # In between.
        c_inverted = OrGate(self.a, self.b)
        c = NotGate(c_inverted)

        f_inverted = OrGate(NotGate(OrGate(self.a, c)),
                            NotGate(OrGate(c, self.b)))
        f = NotGate(f_inverted)
        g_inverted = OrGate(self.carry_in, f)
        g = NotGate(g_inverted)

        # Outputs
        carry_out_inverted = OrGate(c, g)
        self.carry_out = NotGate(carry_out_inverted)
        sum_inverted = OrGate(NotGate(OrGate(f, g)),
                              NotGate(OrGate(g, self.carry_in)))
        self.sum = NotGate(sum_inverted)

    def __call__(self, a, b, carry_in):
        """Return (sum, carry_out)"""
        self.a.set(a)
        self.b.set(b)
        self.carry_in.set(carry_in)

        return self.sum.output, self.carry_out.output

    @property
    def outputs(self) -> dict:
        """The outputs of this component."""
        return {
            'sum': self.sum,
            'carry_out': self.carry_out,
        }


class AdderNBit:
    """An N-bit adder using only NOR (a universal logic gate)."""

    FULL_ADDER_CLASS = FullAdderNorOnly
    BIT_LENGTH = 8  # Default

    def __init__(self, bits_a=None, bits_b=None):
        # Inputs
        self.bits_a = bits_a or [
            Input(f'a{i}') for i in range(self.BIT_LENGTH)]
        self.bits_b = bits_b or [
            Input(f'b{i}') for i in range(self.BIT_LENGTH)]

        # This is an internal input.
        self.initial_carry = Input('carry_init')
        self.initial_carry.set(0)

        # Build up the outputs.
        self.bits_sum = []
        carry_in = self.initial_carry
        for bit_a, bit_b in zip(self.bits_a, self.bits_b):

            # Ideally, I would like this to be able to unpack into the sum
            # and carry out, but that involves __getitem__ and __len__ or the
            # like.
            adder = self.FULL_ADDER_CLASS(bit_a, bit_b, carry_in)
            bit_sum, carry_out = adder.sum, adder.carry_out
            self.bits_sum.append(bit_sum)
            carry_in = carry_out

    def __call__(self, a, b):
        """Return (a + b) as an integer."""
        if a < 0:
            raise ValueError("'a' must be positive integer.")
        if b < 0:
            raise ValueError("'b' must be positive integer.")

        max_value = 2 ** self.BIT_LENGTH - 1
        bit_count = self.BIT_LENGTH

        if a.bit_length() > self.BIT_LENGTH:
            raise ValueError(
                f"'a' must be less than {max_value} ({bit_count}-bit unsigned "
                "integer).")
        if b.bit_length() > self.BIT_LENGTH:
            raise ValueError(
                f"'b' must be less than {max_value} ({bit_count}-bit unsigned "
                "integer).")

        # Convert integer to bits and set the inputs.
        for a, a_in in zip(reversed(self.integer_to_bool_array(
                                        a, self.BIT_LENGTH)),
                           self.bits_a):
            a_in.set(a)
        for b, b_in in zip(reversed(self.integer_to_bool_array(
                                        b, self.BIT_LENGTH)),
                           self.bits_b):
            b_in.set(b)

        if any(bit.output is None for bit in self.bits_sum):
            raise RuntimeError('An output was not set.')

        return self.bool_array_to_integer(
            bit.output for bit in reversed(self.bits_sum))

    @staticmethod
    def integer_to_bool_array(integer, bit_length=8):
        """Return a boolean array representing the integer.

        The most signifiant bit will be at index 0.
        """
        return [bool(integer & (1 << (bit_length - 1 - n)))
                for n in range(bit_length)]

    @staticmethod
    def bool_array_to_integer(bool_array):
        """Returns an integer based on the bits set in the boolean array.

        This expects the most signifiant bit to at index 0 of the array.
        """
        value = 0
        for bit in bool_array:
            value = (value << 1) | bit
        return value

    @property
    def outputs(self) -> dict:
        """The outputs of this component."""
        return {f'sum{i}': bit for i, bit in enumerate(self.bits_sum)}


class Adder8Bit(AdderNBit):
    """An 8-bit adder using only XOR, AND and OR gates."""

    FULL_ADDER_CLASS = FullAdder
    BIT_LENGTH = 8


class Adder8BitUniversal(AdderNBit):
    """An 8-bit adder using only NOR (a universal logic gate)."""

    FULL_ADDER_CLASS = FullAdderNorOnly
    BIT_LENGTH = 8


class Adder16BitUniversal(AdderNBit):
    """An 16-bit adder using only NOR (a universal logic gate)."""

    FULL_ADDER_CLASS = FullAdderNorOnly
    BIT_LENGTH = 16


class IntegerToBinary:
    """Represents the component that takes an integer and converts them to
    individual booleans (bits)."""

    # This class is an component for dealing with the conversion to digital
    # logic.
    #
    # The design of the class isn't quite right for fitting with the evaluation
    # logic, as it really needs a higher level thing to recognise this should
    # be set and then propagate along.

    def __init__(self, name, bit_length=8):
        self.bit_length = bit_length
        self._outputs = [Output(f'{name}{i}', self, i)
                         for i in range(self.bit_length)]

    @property
    def outputs(self):
        return {
            f'bit{i}': bit for i, bit in enumerate(self._outputs)
        }

    def set(self, value):
        values = reversed(self.integer_to_bool_array(value, self.bit_length))
        for output, value in zip(self._outputs, values):
            output.set(value)

    @staticmethod
    def integer_to_bool_array(integer, bit_length=8):
        """Return a boolean array representing the integer.

        The most signifiant bit will be at index 0.
        """
        return [bool(integer & (1 << (bit_length - 1 - n)))
                for n in range(bit_length)]


class Visitor:
    """Implements a form of the visitor pattern to walk over components."""

    def __init__(self, connections=True):
        self.handle_connections = connections
        self.visit_nodes_once = True

        # If visit nodes once is True then keep track of what nodes have
        # been seen so they are only accepted once.
        self.seen_nodes = set()

    def accept(self, gate_or_input, name=None):
        if self.visit_nodes_once and id(gate_or_input) in self.seen_nodes:
            return

        self.seen_nodes.add(id(gate_or_input))

        if isinstance(gate_or_input, BinaryGate):
            gate = gate_or_input

            self.accept_gate(gate, name)

            self.accept(gate.a)
            self.accept(gate.b)

            if self.handle_connections:
                # TODO: Should this handle connections from Output or let
                # everyone deal with that in accept_connection?

                # Binary gate only has one output so the destination is 0.
                self.accept_connection(gate.a, gate, 0, 0)
                self.accept_connection(gate.b, gate, 1, 0)
        elif isinstance(gate_or_input, NotGate):
            # This could be generalised to be an unary gate (1 input with
            # 1 output.).
            gate = gate_or_input
            self.accept_gate(gate, name)
            self.accept(gate.a)
            if self.handle_connections:
                self.accept_connection(gate.a, gate, 0, 0)
        elif isinstance(gate_or_input, Input):
            self.accept_input(gate_or_input)
        elif isinstance(gate_or_input, Output):
            # Outputs are not represented as their own thing. However, this
            # needs to ensure the component it is part of is visited.
            self.accept(gate_or_input.component)
        elif hasattr(gate_or_input, 'outputs'):
            # This is a component that has the result of gates as their output.
            component = gate_or_input
            self.enter_component(component, name)
            for name, gate in component.outputs.items():
                if isinstance(gate, list):
                    for sub_gate in gate:
                        self.accept(sub_gate)
                else:
                    self.accept(gate, name)
            self.leave_component(component, name)

            sources = getattr(gate_or_input, 'inputs', None)
            if self.handle_connections and sources:
                # The key of the sources is a name of the inputs.
                # The value of the sources is the 'gate'/'component'.

                # Handle sources being a dictionary or a sequence.
                if isinstance(sources, dict):
                    sources = sources.values()

                for i, source in enumerate(sources):
                    self.accept_connection(source, component, i, 0)
        else:
            # The idea here is to provide a 'Gate' abstraction so there is
            # a generic inputs and outputs property for gates, like wise
            # for 'components'
            raise NotImplementedError(
                f'Unhandled type {type(gate_or_input)} - {gate_or_input}')

    def accept_input(self, input):
        raise NotImplementedError('Derived class should implement')

    def accept_gate(self, gate, name=None):
        raise NotImplementedError('Derived class should implement')

    def accept_connection(self, source, destination,
                          source_index, destination_index):
        raise NotImplementedError('Derived class should implement')

    def enter_component(self, component, name):
        # Optional - derived class may choose to override this function.
        pass

    def leave_component(self, component, name):
        # Optional - derived class may choose to override this function.
        pass


def graph(component, writer):
    """Generate a GraphViz Dot graph representing the gates in the component.
    """
    class OutputNodes(Visitor):
        def __init__(self):
            super().__init__(connections=False)

        def accept_input(self, input):
            writer.write(
                f'  node_{id(input):x} '
                f'[shape=invhouse, label="{input.name}"]\n')

        def accept_gate(self, gate, name=None):
            name = name or gate.__class__.__name__
            writer.write(
                f'  node_{id(gate):x} [shape=box, label="{name}", ' +
                'width=3, height=2]\n')

        def enter_component(self, component, name=None):
            # This needs to describe a group / sub-graph.
            name = name or component.__class__.__name__
            writer.write(
                f'  node_{id(component):x} [shape=octagon, label="{name}", ' +
                'width=3, height=2]\n')

    class OutputEdges(Visitor):
        def accept_input(self, input):
            # Nothing to do, as the edge must have been referred to by a gate.
            pass

        def accept_gate(self, gate, name=None):
            pass

        def accept_connection(self, source, destination,
                              source_index, destination_index):
            if isinstance(source, Output):
                # The node the connection is from is component, however the
                # port it is connected to is source.
                source = source.component

            writer.write(
                f'  node_{id(source):x} -> node_{id(destination):x}\n')

    # This only graphs path reachable from the outputs.
    writer.write(f'digraph {component.__class__.__name__} {{\n')

    # Visit each node and write them out. Do this first.
    OutputNodes().accept(component)

    # Visit the edges and write them edges.
    OutputEdges().accept(component)

    writer.write('}')


class NotGateTests(unittest.TestCase):
    """Tests the functionality of the Not class."""

    def test_call(self):
        """Test the call operator on the NotGate class"""
        gate = NotGate(Input("a"))
        self.assertEqual(gate(True), False)
        self.assertEqual(gate(False), True)

    def test_nor_populate_input_false(self):
        """Test not gate by setting input to False."""
        a = Input('a')
        gate = NotGate(a)

        a.set(False)
        self.assertEqual(gate.output, True)

    def test_nor_populate_input_false(self):
        """Test not gate by setting input to True."""
        a = Input('a')
        gate = NotGate(a)

        a.set(True)
        self.assertEqual(gate.output, False)


class NorGateTests(unittest.TestCase):
    """Tests the functionality of the NorGate class."""

    def test_nor_call(self):
        """Test the call operator on nor gate."""
        gate = NorGate(Input('a'), Input('b'))
        self.assertEqual(gate(False, False), True)
        self.assertEqual(gate(False, True), False)
        self.assertEqual(gate(True, False), False)
        self.assertEqual(gate(True, True), False)

    def test_nor_populate_input_00(self):
        """Test nor gate going by setting inputs (False, False)."""
        a = Input('a')
        b = Input('b')
        gate = NorGate(a, b)

        a.set(False)
        b.set(False)
        self.assertEqual(gate.output, True)

    def test_nor_populate_input_01(self):
        """Test nor gate going by setting inputs (False, True)."""
        a = Input('a')
        b = Input('b')
        gate = NorGate(a, b)

        a.set(False)
        b.set(True)
        self.assertEqual(gate.output, False)

    def test_nor_populate_input_10(self):
        """Test nor gate going by setting inputs (True, False)."""
        a = Input('a')
        b = Input('b')
        gate = NorGate(a, b)
        a.set(True)
        b.set(False)
        self.assertEqual(gate.output, False)

    def test_nor_populate_input_11(self):
        """Test nor gate going by setting inputs (True, True)."""
        a = Input('a')
        b = Input('b')
        gate = NorGate(a, b)
        a.set(True)
        b.set(True)
        self.assertEqual(gate.output, False)

    def test_nor_str(self):
        """Test nor gate's string representation."""
        gate = NorGate(Input('a'), Input('b'))
        self.assertEqual(str(gate), "NorGate(a, b)")

    def test_nor_repr(self):
        """Test nor gate's string representation."""
        gate = NorGate(Input('a'), Input('b'))
        self.assertEqual(repr(gate), "NorGate(Input('a'), Input('b'))")


class OrGateTests(unittest.TestCase):
    """Tests the functionality of the OrGate class."""

    def test_or_populate_input_00(self):
        """Test or gate going by setting inputs (False, False)."""
        a = Input('a')
        b = Input('b')
        gate = OrGate(a, b)

        a.set(False)
        b.set(False)
        self.assertEqual(gate.output, False)

    def test_or_populate_input_01(self):
        """Test or gate going by setting inputs (False, True)."""
        a = Input('a')
        b = Input('b')
        gate = OrGate(a, b)

        a.set(False)
        b.set(True)
        self.assertEqual(gate.output, True)

    def test_or_populate_input_10(self):
        """Test or gate going by setting inputs (True, False)."""
        a = Input('a')
        b = Input('b')
        gate = OrGate(a, b)
        a.set(True)
        b.set(False)
        self.assertEqual(gate.output, True)

    def test_or_populate_input_11(self):
        """Test or gate going by setting inputs (True, True)."""
        a = Input('a')
        b = Input('b')
        gate = OrGate(a, b)
        a.set(True)
        b.set(True)
        self.assertEqual(gate.output, True)

    def test_or_str(self):
        """Test or gate's string representation."""
        gate = OrGate(Input('a'), Input('b'))
        self.assertEqual(str(gate), "OrGate(a, b)")

    def test_or_repr(self):
        """Test or gate's string representation."""
        gate = OrGate(Input('a'), Input('b'))
        self.assertEqual(repr(gate), "OrGate(Input('a'), Input('b'))")


class XorGateTests(unittest.TestCase):
    """Tests the functionality of the XorGate class."""

    def test_xor_populate_input_00(self):
        """Test xor gate going by setting inputs (False, False)."""
        a = Input('a')
        b = Input('b')
        gate = XorGate(a, b)

        a.set(False)
        b.set(False)
        self.assertEqual(gate.output, False)

    def test_xor_populate_input_01(self):
        """Test xor gate going by setting inputs (False, True)."""
        a = Input('a')
        b = Input('b')
        gate = XorGate(a, b)

        a.set(False)
        b.set(True)
        self.assertEqual(gate.output, True)

    def test_xor_populate_input_10(self):
        """Test xor gate going by setting inputs (True, False)."""
        a = Input('a')
        b = Input('b')
        gate = XorGate(a, b)
        a.set(True)
        b.set(False)
        self.assertEqual(gate.output, True)

    def test_xor_populate_input_11(self):
        """Test xor gate going by setting inputs (True, True)."""
        a = Input('a')
        b = Input('b')
        gate = XorGate(a, b)
        a.set(True)
        b.set(True)
        self.assertEqual(gate.output, False)

    def test_xor_str(self):
        """Test xor gate's string representation."""
        gate = XorGate(Input('a'), Input('b'))
        self.assertEqual(str(gate), "XorGate(a, b)")

    def test_xor_repr(self):
        """Test xor gate's string representation."""
        gate = XorGate(Input('a'), Input('b'))
        self.assertEqual(repr(gate), "XorGate(Input('a'), Input('b'))")


class AndGateTests(unittest.TestCase):
    """Tests the functionality of the AndGate class."""

    def test_and_populate_input_00(self):
        """Test and gate going by setting inputs (False, False)."""
        a = Input('a')
        b = Input('b')
        gate = AndGate(a, b)

        a.set(False)
        b.set(False)
        self.assertEqual(gate.output, False)

    def test_and_populate_input_01(self):
        """Test and gate going by setting inputs (False, True)."""
        a = Input('a')
        b = Input('b')
        gate = AndGate(a, b)

        a.set(False)
        b.set(True)
        self.assertEqual(gate.output, False)

    def test_and_populate_input_10(self):
        """Test and gate going by setting inputs (True, False)."""
        a = Input('a')
        b = Input('b')
        gate = AndGate(a, b)
        a.set(True)
        b.set(False)
        self.assertEqual(gate.output, False)

    def test_and_populate_input_11(self):
        """Test and gate going by setting inputs (True, True)."""
        a = Input('a')
        b = Input('b')
        gate = AndGate(a, b)
        a.set(True)
        b.set(True)
        self.assertEqual(gate.output, True)

    def test_and_str(self):
        """Test and gate's string representation."""
        gate = AndGate(Input('a'), Input('b'))
        self.assertEqual(str(gate), "AndGate(a, b)")

    def test_and_repr(self):
        """Test and gate's string representation."""
        gate = AndGate(Input('a'), Input('b'))
        self.assertEqual(repr(gate), "AndGate(Input('a'), Input('b'))")


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
            expected_sum, carry_out = outputs
            with self.subTest(a=inputs[0], b=inputs[1], carry_in=inputs[2]):
                full_adder = FullAdder()
                actual_sum, actual_carry_out = full_adder(*inputs)
                self.assertEqual(actual_sum, bool(expected_sum))
                self.assertEqual(actual_carry_out, bool(carry_out))

    def test_full_adder_nor(self):
        """Test the full adder using nor only."""
        for inputs, outputs in self.FULL_ADDER_TRUTH_TABLE:
            expected_sum, carry_out = outputs
            with self.subTest(a=inputs[0], b=inputs[1], carry_in=inputs[2]):
                full_adder = FullAdderNorOnly()
                actual_sum, actual_carry_out = full_adder(*inputs)
                self.assertEqual(actual_sum, bool(expected_sum))
                self.assertEqual(actual_carry_out, bool(carry_out))

    def test_full_adder_or_and_not(self):
        """Test the full adder using only ors and nots"""
        for inputs, outputs in self.FULL_ADDER_TRUTH_TABLE:
            expected_sum, carry_out = outputs
            with self.subTest(a=inputs[0], b=inputs[1], carry_in=inputs[2]):
                full_adder = FullAdderOrAndNotOnly()
                actual_sum, actual_carry_out = full_adder(*inputs)
                self.assertEqual(actual_sum, bool(expected_sum))
                self.assertEqual(actual_carry_out, bool(carry_out))

    def test_adder_8bit(self):
        """Test the 8-bit adder performing simple calculations."""
        self.assertEqual(Adder8Bit()(2, 5), 7)
        self.assertEqual(Adder8Bit()(35, 109), 144)

        # Test (0 to N) + 0
        for i in range(256):
            self.assertEqual(Adder8Bit()(i, 0), i)

        # Test 0 + (0 to N)
        for i in range(256):
            self.assertEqual(Adder8Bit()(0, i), i)

    @unittest.skip('Slow test')
    def test_adder_8bit_every_combination(self):
        """Test every possible combination that doesn't overflow."""
        for x in range(256):
            for y in range(256 - x):
                with self.subTest(a=x, b=y):
                    self.assertEqual(Adder8Bit()(x, y), x + y)

    def test_adder_8bit_universal(self):
        """Test the 8-bit adder performing simple calculations."""
        self.assertEqual(Adder8BitUniversal()(2, 5), 7)
        self.assertEqual(Adder8BitUniversal()(35, 109), 144)

        # Test (0 to N) + 0
        for i in range(256):
            self.assertEqual(Adder8BitUniversal()(i, 0), i)

        # Test 0 + (0 to N)
        for i in range(256):
            self.assertEqual(Adder8BitUniversal()(0, i), i)

    @unittest.skip('Slow test')
    def test_adder_8bit_universal_every_combination(self):
        """Test every possible combination that doesn't overflow."""
        for x in range(256):
            for y in range(256 - x):
                with self.subTest(a=x, b=y):
                    self.assertEqual(Adder8BitUniversal()(x, y), x + y)

    def test_adder_16bit_universal(self):
        """Test the 8-bit adder performing simple calculations."""
        self.assertEqual(Adder16BitUniversal()(1000, 3000), 4000)

    def test_output(self):
        """Tests the evaluation handling for Output class via IntegerToBinary.
        """
        a = IntegerToBinary('a')
        b = IntegerToBinary('b')
        adder = Adder8BitUniversal(a.outputs.values(), b.outputs.values())

        a.set(102)
        b.set(149)

        values = [output.output for output in adder.outputs.values()]

        value = Adder8BitUniversal.bool_array_to_integer(reversed(values))
        self.assertEqual(value, 251)


class GraphTests(unittest.TestCase):
    """Tests the components can be graphed.

    This does not check the exact dot output, merely if no exception is raised.
    """

    def test_full_adder_or_and_not_graph(self):
        """Test the full adder using only ors and nots"""
        with io.StringIO() as writer:
            graph(FullAdderNorOnly(), writer)

    def test_full_adder_or_and_not_graph(self):
        """Test the full adder using only ors and nots"""
        with io.StringIO() as writer:
            graph(FullAdderOrAndNotOnly(), writer)


if __name__ == '__main__':
    # unittest.main()
    with open('full_adder_nor_only.gv', 'w') as writer:
        graph(FullAdderNorOnly(), writer)

    with open('adder_8bit.gv', 'w') as writer:
        graph(Adder8Bit(), writer)
