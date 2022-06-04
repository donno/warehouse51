"""Provides tooling for working with a virtual machine for digital circuits.

This uses the construct library to parse the binary format that is used to
encode the circuits. The library is also used to build them.

See virtual_machine.md for more details.
"""

import unittest
import enum
import itertools
import io

import construct


FILE_FORMAT_VERSION = 0


class Opcode(enum.IntEnum):
    """Defines the opcode (operation codes) used in the machine.

    The opcode can have a value from 0 to 255 (single 8-bit byte).
    """
    NOP = 0
    INVERT = 1
    BITWISE_OR = 2
    BITWISE_AND = 3
    BITWISE_XOR = 4
    BITWISE_NOR = 5
    RETURN = 6


class ArgumentType(enum.IntEnum):
    """Defines the type used for the arguments of a symbol."""
    VOID = 0
    BIT = 1


OPCODE_TO_MNEMONIC = {
    Opcode.NOP: 'nop',
    Opcode.INVERT: 'not',
    Opcode.BITWISE_OR: 'or',
    Opcode.BITWISE_AND: 'and',
    Opcode.BITWISE_NOR: 'nor',
    Opcode.RETURN: 'ret',
}


symbol_entry = construct.Struct(
    "argument_count" / construct.Int8ub,
    "arguments" / construct.Array(
        construct.this.argument_count,
        construct.Enum(construct.Int8ub, ArgumentType)),
    "name" / construct.PascalString(construct.VarInt, "utf8"),
    "start" / construct.Int16ub,  # Offset into "instructions"
    # I don't think Construct's Pointer can be used for this.
    # "start" / Pointer(8, Bytes(1)),
    # For debug purposes this could potentially contain argument names.
    # Or have a separate 'debug' entry for details only needed for debugging
    # or reverse-engineering.
)

instruction_definition = construct.Struct(
    "opcode" / construct.Enum(construct.Byte, Opcode),
    "operand_a" / construct.Int8ub,
    "operand_b" / construct.Int8ub,
    "reserved" / construct.Const(0xFF, construct.Int8ub),
)

binary = construct.Struct(
    "signature" / construct.Const(b"DC"),
    "features" / construct.Default(construct.Int16ub, 0),
    "version" / construct.Default(construct.Byte, FILE_FORMAT_VERSION),
    "reserved" / construct.Const(0xCD, construct.Int8ub),
    "symbol_count" / construct.Int8ub,
    "symbols" / construct.Array(construct.this.symbol_count, symbol_entry),
    "instruction_count" / construct.Int16ub,
    "instructions" / construct.Array(construct.this.instruction_count,
                                     instruction_definition),
)


def binary_to_textual(source, writer: io.TextIOBase):
    """Convert a file in binary format to textual format."""
    parsed = binary.parse(source)
    writer.write(f'// Digital Circuit File - version {parsed.version}\n')
    if parsed.features:
        raise NotImplementedError('Process features.')
        # writer.write(f'// Features: NYI')

    def name_generator():
        """Yields the name of the next parameter."""
        for next_index in itertools.count():
            index = next_index
            name = ''
            while index > 0:
                index, remainder = divmod(index - 1, 26)
                name = chr(remainder + ord('a')) + name
                yield name

    def format_arguments(arguments, names):
        if len(arguments) > 25:
            raise NotImplementedError('Labelling more than 25 arguments '
                                      'not supported.')

        return ', '.join(
            f'{arg.lower()} %{name}' for arg, name, in zip(arguments, names)
        )

    if len(parsed.symbols) > 2:
        # For this to work being symbols need to refer to what instructions
        # are for them.
        raise NotImplementedError('Only supports 1 symbol.')

    for symbol in parsed.symbols:
        names = name_generator()

        arguments = format_arguments(symbol.arguments, names)
        # TODO: need to find the return value in the instructions.
        # TODO: Consider putting this in the symbol format or instruction count
        # for the symbol so its O(1) look-up.
        # return_values = format_arguments(symbol.arguments)
        return_values = 'bit sum, bit carry_out'
        writer.write(f'define @{symbol.name}({arguments}) : {return_values}\n')
        writer.write('{\n')

        names = list(itertools.islice(name_generator(), symbol.argument_count))

        for instruction, name in zip(parsed.instructions[symbol.start:],
                                     name_generator()):
            mnemonic = OPCODE_TO_MNEMONIC[instruction.opcode.intvalue]
            operand_a = names[-instruction.operand_a]
            operand_b = names[-instruction.operand_b]

            names.append(name)

            if instruction.opcode.intvalue == Opcode.RETURN:
                writer.write(f'  {mnemonic} %{operand_a} %{operand_b}\n')
                # Only single return per-symbol/function.
                break

            writer.write(
                f'  %{name} = {mnemonic} %{operand_a} %{operand_b}\n')

        writer.write('}\n')


def sample_program_full_adder():
    """Return a sample program - 'fullader' in the binary format."""
    def _instruction(opcode: Opcode, operand_a, operand_b):
        return {'opcode': opcode, 'operand_a': operand_a,
                'operand_b': operand_b}

    return binary.build({
        'symbol_count': 1,
        'symbols': [
            {
                'argument_count': 3,
                'arguments': [ArgumentType.BIT] * 3,
                'name': 'full_adder',
                'start': 0,
            }],
        'instruction_count': 10,
        'instructions': [
            # The index refers the result of instruction to use as an
            # argument, where 1 is the previous instruction, 2 is two
            # instructions ago and so forth.
            #
            # However the arguments are considered the instructions, i.e
            # image they were 'load value' when it comes time to execution.
            _instruction(Opcode.BITWISE_NOR, 3, 2),
            _instruction(Opcode.BITWISE_NOR, 4, 2),
            _instruction(Opcode.BITWISE_NOR, 4, 1),

            _instruction(Opcode.BITWISE_NOR, 2, 1),
            _instruction(Opcode.BITWISE_NOR, 5, 1),

            _instruction(Opcode.BITWISE_NOR, 5, 1),  # This is carry out.

            _instruction(Opcode.BITWISE_NOR, 3, 2),
            _instruction(Opcode.BITWISE_NOR, 3, 8),
            _instruction(Opcode.BITWISE_NOR, 2, 1),  # sum

            _instruction(Opcode.RETURN, 1, 4)
        ],
    })


class BinaryFormatTests(unittest.TestCase):
    """Tests for building and parsing the binary format for digital circuits.
    """

    def test_build_parse_example(self):
        """Test with binary with symbol table and no instructions."""

        # If there are no instructions there should ought to be no symbols but
        # this is just a test of the file format.
        example = binary.build({
            'symbol_count': 1,
            'symbols': [
                {
                    'argument_count': 1,
                    'arguments': [0],
                    'name': 'main',
                    'start': 0,
                }],
            'instruction_count': 0,
            'instructions': [],
        })

        parsed = binary.parse(example)

        self.assertEqual(len(parsed.symbols), 1)
        self.assertEqual(parsed.symbols[0].name, 'main')

    def test_instructions(self):
        """Test with binary with instructions."""
        example = binary.build({
            'symbol_count': 0,
            'symbols': [],
            'instruction_count': 4,
            'instructions': [
                {'opcode': Opcode.NOP, 'operand_a': 0, 'operand_b': 0},
                {'opcode': Opcode.NOP, 'operand_a': 0, 'operand_b': 0},
                {'opcode': Opcode.NOP, 'operand_a': 0, 'operand_b': 0},
                {'opcode': Opcode.RETURN, 'operand_a': 0, 'operand_b': 0},
            ],
        })

        parsed = binary.parse(example)

        self.assertEqual(len(parsed.instructions), 4)

    def test_full_adder(self):
        """Test with a sample program for a full adder."""
        example = sample_program_full_adder()
        parsed = binary.parse(example)

        # Check symbol table first.
        self.assertEqual(len(parsed.symbols), 1)
        self.assertEqual(parsed.symbols[0].name, 'full_adder')

        self.assertEqual(len(parsed.symbols[0].arguments), 3)
        self.assertEqual(
            parsed.symbols[0].arguments[0].intvalue, ArgumentType.BIT)
        self.assertEqual(
            parsed.symbols[0].arguments[1].intvalue, ArgumentType.BIT)
        self.assertEqual(
            parsed.symbols[0].arguments[2].intvalue, ArgumentType.BIT)


if __name__ == '__main__':
    unittest.main()

    # with io.StringIO() as writer:
    #     binary_to_textual(sample_program_full_adder(), writer)
    #     print(writer.getvalue())
