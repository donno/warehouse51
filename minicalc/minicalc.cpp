//===----------------------------------------------------------------------===//
//
// NAME         : minicalc
// PURPOSE      : An experiment in different ways of implementing a simple
//                computer.
// COPYRIGHT    : (c) 2017 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// STATUS       : Unfinished
// DESCRIPTION  : This intends to module a simple computer like the "Little Man
//                computer" which is used as a teaching aid for machine using
//                von Neumann architecture (data and instructions share same
//                memory space/address lines.).
//
// See  https://en.wikipedia.org/wiki/Little_man_computer
//
// Essentially, this was something I played around with for a couple of days
// in 2017 and simply filled out a few more details in 2021.
//
//===----------------------------------------------------------------------===//

// The following is provided as-is,
//
// Types of machines:
// - immediate - the operation is resolved straight away
// - delayed - the operation is resolved when ImmediateMachine::result() is called.
#include <vector>

class ImmediateMachine
{
public:
    ImmediateMachine() : myAccumulator(0) {}

    void add(int value);
    void subtract(int value);
    void multiply(int value);
    void divide(int value);

    int result() const { return myAccumulator; }

private:
    int myAccumulator;
};

class DelayedMachine
{
public:

    void add(int value);
    void subtract(int value);
    void multiply(int value);
    void divide(int value);

    int result() const;

private:
    enum class Operation
    {
        Add,
        Subtract,
        Multiply,
        Divide,
    };

    struct Op
    {
        Op(Operation operation, int operand)
        : myOperation(operation), myOperand(operand) {}

        Operation myOperation;
        int myOperand;
    };

    std::vector<Op> myOperations;
};

#include <iostream>

/////////// ImmediateMachine

void ImmediateMachine::add(int value)
{
    myAccumulator += value;
}

void ImmediateMachine::subtract(int value)
{
    myAccumulator -= value;
}

void ImmediateMachine::multiply(int value)
{
    myAccumulator *= value;
}

void ImmediateMachine::divide(int value)
{
    myAccumulator /= value;
}

/////////// End of ImmediateMachine

/////////// DelayedMachine

void DelayedMachine::add(int value)
{
    myOperations.emplace_back(Operation::Add, value);
}

void DelayedMachine::subtract(int value)
{
    myOperations.emplace_back(Operation::Subtract, value);
}

void DelayedMachine::multiply(int value)
{
    myOperations.emplace_back(Operation::Multiply, value);
}

void DelayedMachine::divide(int value)
{
    myOperations.emplace_back(Operation::Divide, value);
}

int DelayedMachine::result() const
{
    int accumulator = 0;
    for (const auto& operation : myOperations)
    {
        switch (operation.myOperation)
        {
        case Operation::Add:
            accumulator += operation.myOperand;
            break;
        case Operation::Subtract:
            accumulator -= operation.myOperand;
            break;
        case Operation::Multiply:
            accumulator *= operation.myOperand;
            break;
        case Operation::Divide:
            accumulator /= operation.myOperand;
            break;
        }
    }

    return accumulator;
}

/////////// End of DelayedMachine

const auto calculate = [](auto machine)
{
    machine.add(5);
    machine.add(2);
    machine.subtract(1);
    machine.multiply(2);
    machine.divide(3);

    return machine.result();
};

int main()
{
    {
        ImmediateMachine machine;
        std::cout << "Result: " << calculate(machine) << std::endl;
    }

    {
        DelayedMachine machine;
        std::cout << "Result: " << calculate(machine) << std::endl;
    }

    return 0;
}
