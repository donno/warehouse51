Virtual Machine
===============

The intention here is to design a byte-code / instruction set for describing
basic digital circuits and an virtual machine to execute it.

A non-goal is to develop a system that can handle the parallelism or pipeline
operations that can happen at the same time due to non-dependencies.
If this was to be done it would be done via vectorisation / single-instruction
multi-data as other wise the the overhead to simulate that would be greater
than running it in series.

Implementation
--------------
Not started

Basic ideas
-----------
* Fixed length instruction
* 8-bit Op-code

File format
-----------
* Textual - digital circuit text - .dct
* Binary - digital circuit binary - .dcb

### Textual
This provides a textual representation where mnemonics are used instead of
op-codes. Essentially, this is like an assembly language.

The intention is to use this as a way describe systems / algorithms so primarily
for documentation as well as using it as a disassemble form of the binary.

Ideas
- Use single static assignment
  This means you can't have:  nor(nor(a, c), nor(c, b)), the inner two nor
  would be written on as its own assignment.

Example:
```
define @full_adder(bit %a, bit %b, bit %carry_in) : bit sum, bit carry_out
{
    %c = nor %a, %b

    %d = nor %a, %carry_in
    %e = nor %b, %d
    %f = nor %d, %e

    %g = nor %carry_in, %f

    %carry_out = nor %c %g

    %h = nor %f, %g
    %i = nor %g, %carry_in

    %sum = nor %h, %i

    ret $sum, %carry_out
}
```

In the above example, the variable names likely would be %0 to %N if generated
from higher-level definition of a full adder.

### Binary

One idea is to use Kaitai Struct (https://kaitai.io) to document this.

* Header
    * Magic number (2-bytes)
      'DC' or 0x4443
    * Features (2-bytes)
      0x0000 (Base feature set)
    * Version number (1-byte)
      0x00 (Version 0)
    * Reserved (1-bytes)
      0xCD
    * Symbol table (OR) Offset to symbol table (2-bytes)
    * Instruction Size (4-bytes)
    * Instructions

* Instruction
    * Op code (1-byte)
    * Operand A (1-byte)
    * Operand B (1-byte)
    * Reserved (1-byte)

* Symbol table
    * Symbol count (1 byte)
    * Argument count (1-byte)
    * Argument types (1-byte * (Argument count)
    * Symbol name (length first rather than null-terminated).
      Alternatively, put all the strings at the end of the symbol table so this
      becomes a offset to them.

### Op Codes
TODO: Convert this to a table where it is: Name, mnemonic and byte (hex).

* No-op
* Invert (not)
* Bit-wise or
* Bit-wise and
* Bitwise xor
* Bitwise nor
* Return


Open Questions
--------------
- How to handle concurrency?
  If there are two functions where one calls the other, would it be possible
  to start both functions but suspend one once it hits an instruction that
  needs the result of the other. If so when producing the binary form does it
  re-order instructions to allow the most number of instructions to run first.
- Register-based or Stack-based?

Design Decisions
----------------

### Register-based or Stack-based?

Pros of stack-based
* Limits how much addressing is required.
* Easy to return multiple values - the values left on the stack on return are
  the values returned.

Con of stack-based
* Requires reordering instructions
* Harder to re-use results - unless each operation had a way to say keep
  last-value and/or swap them.
* Less of a connection to the original source.

Pros of register-based
* Easier to map to from static single assignment form.
* Closer to the source

Cons of register-based
* Additional complications if there are fixed number of registers.
  Requires determining how many results to keep around and thus if instructions
  can be re-order to reduce register pressure.

Stack-based example
* push a (argument 0)
* push b (argument 1)
* nor
* push carry_in (argument 2)
* nor
* push b (argument 1)
* nor  # So this is nor (nor (nor a, b), carry), b
* ...
* TODO: Finish the example to show what full_adder would look like.


### Operands
Currently the plan is to try out idea 2.

Idea 1
* Positive numbers refer to function parameter.
* Negative numbers reference previous computations.
  This also means past results would be accumulated.

The space is not very well balanced as functions (symbols) would only have a
small number of parameters, yet half the index space would be reserved for
them.

The negative numbers are essentially relative so it means they could have
a lot of instructions but limit these offsets to smaller space.

Alternatively, could have a long/short form with the fourth unused byte.

Idea 2
* Numbers reference previous computations.
* The function parameters are considered as the first three previous
  computations.
* Doesn't suffer the split of negative and positive numbers from idea 1.
