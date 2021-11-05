"""Numberhunt is a hunt for the algebraic expression to equal a target number.

The rules of the game are:
- A target number is selected. Between 100 and 999 inclusive.
- Six numbers are selected from the pool of [25, 50, 75, 100] and the
  numbers 1 to 10 each appearing twice.
- Using the six numbers attempt to get the target number (or closest) using
  addition, subtraction, multiplication and division.
- All six numbers aren't required.
- Division is only valid if the result is an integer.

Scoring is
- 10 points for the getting the exact solution
- 7 points for 5 away
- 5 points within 10 points
- 0 if neither.

"""

import itertools
import operator
import random
import unittest


__version__ = '1.0.0'
__copyright__ = "Copyright 2019, https://github.com/donno/"


def postfix_calculator(expression: list, partial: bool = False):
    """Evaluates the expression where expression is a mix of numbers and
      operators in posfix form.

      Requirements of the expression and thus posfix notation
      - Two numbers must always appear at the start.
      - An operator must always appear at the end (unless only a single number
        is used).

      Parameters
      ==========
      expression
        The posfix expression as a list of numbers and operators.
        Valid operators are add, mul, floordiv and sub.

      partial
        If true then a partial sum will be evaluated.

      Return
      =======
      int
        The result of the expression if the expression is complete and partial
        is false.
      list
        A partially evaluated expression if partial is false.

      Example
      =======
      The following expression returns 24.
      ```
      postfix_calculator(
          [100, 25, operator.add, 5, operator.floordiv, 1, operator.sub])
      ```
    """

    stack = []

    for op in expression:
        if isinstance(op, int):
            stack.append(op)
        else:
            a = stack.pop()
            b = stack.pop()

            result = op(float(b), float(a))
            if result.is_integer():
                stack.append(int(result))
            else:
                # This is unique to number hunt.
                raise ArithmeticError(
                    'Operation did not result in a whole number')

    if partial:
        return stack

    assert len(stack) == 1
    return stack.pop()


def pretty_expression(expression) -> str:
    """Produce a pretty string form of the expression.

    This means covering operators to equivalent strings like operator.add to +.
    """
    def _pretty_item(item):
        operator_to_name = {
            operator.add: '+',
            operator.sub: '-',
            operator.mul: '*',
            operator.truediv: '/',
            operator.floordiv: '/',
        }
        return operator_to_name.get(item, str(item))

    return ' '.join(_pretty_item(item) for item in expression)


class Game:
    """Implements the game as an act of building up a posix expression using
    up to six numbers chosen from a pool numbers and the add, subtract, divide
    and multiple.
    """

    """The list of all possible numbers that the six selected numbers can
    come from.

    Not implemented here is the players competing against each other can
    choose how many numbers from the large nubmer list (25, 50, 75, 100) to
    pick, it can be zero to four, choosing all 4 guarantees the four numbers
    otherwise its still random. Generally its best to have 1 or 2 large as
    there are more solutions.
    """
    pool = [25, 50, 75, 100] + list(range(1, 11)) + list(range(1, 11))

    operators = [operator.add, operator.floordiv, operator.sub, operator.mul]

    def __init__(self, target=None, numbers=None):
        # The full expression.
        self.expression = []

        # The expression as its been currently evaluated. In practice this
        # means once an operation is done the operation is computed and the
        # operation is evaluated.
        self.evaluated_expression = []

        if numbers and len(numbers) != 6:
            raise ValueError('There must be at least six numbers provided.')
        elif numbers:
            invalid_number = next(
                (number for number in numbers if number not in self.pool),
                None)
            if invalid_number is not None:
                raise ValueError(f'The number {invalid_number} is invalid.\n')

            # This doesn't bother validating duplicates.

        if target:
            self.target = target
        else:
            self.target = random.randint(100, 999)

        if numbers:
            self.numbers = numbers[:]
        else:
            self.numbers = random.sample(self.pool, 6)

        self.numbers.sort(reverse=True)

        # A list of all actions that can be made. Depending on the current
        # state some may not be legal. Use legal_action().
        self.all_actions = self.numbers + self.operators

    def reset(self):
        """Reset the game for a new game."""
        self.target = random.randint(100, 999)
        self.numbers = random.sample(self.pool, 6)
        self.numbers.sort(reverse=True)
        self.all_actions = self.numbers + self.operators
        self.expression = []
        self.evaluated_expression = []

    def legal_actions(self):
        """The list of all legal actions.

        The first two actions must be using a number as all the operators are
        binary and require two numbers.
        """

        # By checking against evaluated_expression instead of expression this
        # checks that there are enough numbers for an operator to be a legal
        # action.

        if not self.evaluated_expression:
            return self.numbers

        if len(self.evaluated_expression) == 1:
            # This assumes that step() removed the number from the expression.
            return self.numbers

        # Check if the divide operator is valid.
        if len(self.evaluated_expression) >= 2:
            if self.evaluated_expression[-1] == 0:
                # The expression would be A / 0 which is not legal.
                legal_operators = self.operators[:]
                legal_operators.remove(operator.floordiv)
                return self.numbers + legal_operators

            if operator.imod(*self.evaluated_expression[-2:]) != 0:
                # The expression A / B would result in a non-integer result.
                # This makes the floordiv operator illegal here.
                legal_operators = self.operators[:]
                legal_operators.remove(operator.floordiv)
                return self.numbers + legal_operators

        return self.numbers + self.operators

    def legal_action_indices(self):
        """The list of all legal actions as indices. This means the list will
        be simple integer in the range 0 to 10 inclusive.

        The set of actions are picking the one of the numbers or picking an
        operation. so 0 to 5 inclusive is the action of picking a number,
        6 to 9 is picking an operator.

        The first two actions must be using a number as all the operators are
        binary and require two numbers.

        To step() using this use all_actions[index] to convert the index to
        the action.
        """
        actions = self.legal_actions()
        return [self.all_actions.index(action) for action in actions]

    def step(self, action):
        """Apply action to the game.

        In this case it means adding the number or operation to the expression.
        """
        assert action in self.legal_actions()

        self.expression.append(action)
        self.evaluated_expression.append(action)

        if isinstance(action, int):
            self.numbers.remove(action)

        # Evaluate the expression when an operator is provided.
        if not isinstance(action, int):
            # An operator was provided.
            self.evaluated_expression = postfix_calculator(
                self.expression, partial=True)

            latest_value = self.evaluated_expression[-1]
            # print('latest_value', latest_value)

        done = self.evaluated_expression[-1] == self.target or (
            not self.legal_actions()  # No more legal moves.
        )

        return self.evaluated_expression[-1] - self.target, done

    def __str__(self):
        return 'Target: {}. Expression: {}'.format(
            self.target, pretty_expression(self.expression))


class NumberHuntTests(unittest.TestCase):

    def test_evaluate(self):
        game = Game(
            target=781,
            numbers=[10, 9, 3, 6, 8, 100],
        )

        game.step(8)
        game.step(100)
        game.step(operator.mul)  # so 8 * 100 is 800

        self.assertEqual(len(game.evaluated_expression), 1)
        self.assertEqual(game.evaluated_expression[0], 800)

    def test_divide_is_not_legal_non_integer(self):
        game = Game(
            target=781,
            numbers=[10, 9, 3, 6, 8, 100],
        )

        game.step(8)
        game.step(100)
        game.step(operator.mul)  # so 8 * 100 is 800
        game.step(3)
        # 800 / 3 would 266.666666667

        self.assertNotIn(operator.floordiv, game.legal_actions())

    def test_divide_is_not_legal_by_zero(self):
        game = Game(
            target=781,
            numbers=[10, 10, 3, 5, 8, 100],
        )

        game.step(100)
        game.step(10)
        game.step(10)
        game.step(operator.sub)  # 10 - 10 is 0.

        # Sitting on the expression stack will be [100, 0].
        self.assertNotIn(operator.floordiv, game.legal_actions())

    def test_legal_actions(self):
        game = Game(
            target=781,
            numbers=[10, 9, 3, 6, 8, 100],
        )

        # The first two sets of legal actions will only be the numbers.
        self.assertEqual(game.legal_actions(), game.numbers)
        game.step(8)

        # Actions is only a number minus the 8.
        self.assertEqual(game.legal_actions(), [100, 10, 9, 6, 3])

        game.step(100)

        # The action should now include the operators but not 8 or 100
        #
        # The divide operator is not valid here operator.floordiv as 8 / 100
        # does not end up with a integer.
        self.assertEqual(
            game.legal_actions(), [10, 9, 6, 3] +
                                  [operator.add, operator.sub, operator.mul])

        game.step(operator.mul)  # so 8 * 100 is 800

        # Operators are not legal at this stage as there is only one number
        # avaliable as an operand and operators require two operands.
        self.assertEqual(game.legal_actions(), [10, 9, 6, 3])

        game.step(3)  # so 800 and 3

        # Multiple is still avaliable even thou it was used before as operators
        # are not single use.
        #
        # If we used 6 instead of 8 original, we could have used divide here
        # is 600 / 3 is legal.
        self.assertEqual(game.legal_actions(),
                         [10, 9, 6] +
                         [operator.add, operator.sub, operator.mul])

    def test_legal_actions_indices(self):
        game = Game(
            target=781,
            numbers=[10, 9, 3, 6, 8, 100],
        )

        # Reminder:
        # - indices [0, 1, 2, 3, 4, 5] are numbers.
        # - indices [6, 7, 8, 9] are operators (+, /, *, -)
        #

        # The first two sets of legal actions will only be the numbers.
        self.assertEqual(game.legal_action_indices(), list(range(6)))

        game.step(game.all_actions[3])

        self.assertEqual(game.legal_action_indices(), [0, 1, 2, 4, 5])

        # The action 3 was picking the number 8 in this case.
        self.assertEqual(8, game.all_actions[3])
        self.assertEqual(game.legal_actions(), [100, 10, 9, 6, 3])

        game.step(game.all_actions[0])

        # The legal actions should now include the operators but not 8 or 100.
        #
        # The divide operator is not valid here operator.floordiv as 8 / 100
        # does not end up with a integer.

        self.assertEqual(game.legal_action_indices(),
                         [1, 2, 4, 5, 6, 8, 9])

        # The action 0 was picking the number 100 in this case.
        self.assertEqual(100, game.all_actions[0])
        self.assertEqual(
            game.legal_actions(),
            [10, 9, 6, 3] + [operator.add, operator.sub, operator.mul])

        game.step(operator.mul)  # so 8 * 100 is 800

        # Operators are not legal at this stage as there is only one number
        # avaliable as an operand and operators require two operands.
        self.assertEqual(game.legal_action_indices(), [1, 2, 4, 5])

        game.step(3)  # so 800 and 3

        # Multiple is still avaliable even thou it was used before as operators
        # are not single use.
        #
        # If we used 6 instead of 8 original, we could have used divide here
        # is 600 / 3 is legal.
        self.assertEqual(game.legal_action_indices(), [1, 2, 4, 6, 8, 9])
        self.assertEqual(game.legal_actions(),
                         [10, 9, 6] +
                         [operator.add, operator.sub, operator.mul])


def generate_possible_expressions(numbers):
    """Generates the possible postfix expressions that can be a applied to
       the given numbers.
    """
    minimum_numbers_to_use = 2
    minimum_numbers_to_use = 4

    def _generate_numbers(numbers):
        for total_number_usage in range(
                minimum_numbers_to_use, len(numbers) + 1):
            for ordered_numbers in itertools.permutations(
                    numbers, r=total_number_usage):
                yield ordered_numbers

    for ordered_numbers in _generate_numbers(numbers):
        operator_count = len(ordered_numbers) - 1
        for operators in itertools.product(Game.operators, repeat=3):
            # Requirements of the posfix notation
            # - An operator must always appear at the end.
            # - Two numbers must always appear at the start.
            start = ordered_numbers[0:2]
            end = operators[-1]

            # TODO: this will produce some duplicated expressions as the
            # numbers were already in a fixed position given by
            # ordered_numbers.
            # Two possible options to improve this:
            # 1) Discard the premutation below of the numbers are not in the
            #    same order they are in ordered_numbers
            # 2) Have the outer loop only generate the first 2 and final number
            #    and leave premutating any other numbers to this bit.

            reorderable = ordered_numbers[2:] + operators[:-1]
            for middle in itertools.permutations(reorderable):
                yield start + middle + (end, )


def solve_brute_force(target, numbers):
    """Solve the problem of how to target target (or closest to it) by
    adding, subtracting, dividing or multiplying the given numbers together.
    """

    def evaluate_expressions(expressions):
        """Evaluate the expressions and filter out any expression that is
        invalid."""
        for expression in expressions:
            try:
                yield expression, postfix_calculator(expression)
            except ZeroDivisionError:
                # Attempted to divide by zero.
                pass
            except IndexError:
                # Expression is either empty or there is not enough items on
                # the stack.
                pass

    expressions = evaluate_expressions(generate_possible_expressions(numbers))
    closest_expression, closest_value = min(
        expressions, key=lambda value: abs(value[1] - target))
    print('[%s] = %d' % (pretty_expression(closest_expression), closest_value))


def solve_brute_force_legal_only(target, numbers):
    # TODO: This needs a better generate_possible_expressions
    def evaluate_expressions(expressions):
        """Evaluate the expressions."""
        for expression in expressions:
            yield expression, postfix_calculator(expression)

    starting_point = Game(
        target=target,
        numbers=numbers,
    )

    # Simple rule is if target is 100 than its possible to win in one move by
    # 100 being a valid number
    if target in numbers:
        return [target]

    raise NotImplementedError('This is not implemented.')

    def legal_possible_expressions(starting_point):
        # The only way for the first action to succeed is if the target is 100
        # and the number 100 was chosen.
        #
        # Otherwise you need at least a minimum of three actions.

        for action in starting_point.legal_actions():
            yield [action]

        for action in starting_point.legal_actions():
            yield [action]

        # yield from generate_possible_expressions(numbers)

    expressions = evaluate_expressions(
        legal_possible_expressions(starting_point))
    closest_expression, closest_value = min(
        expressions, key=lambda value: abs(value[1] - target))
    print('[%s] = %d' % (pretty_expression(closest_expression), closest_value))


if __name__ == '__main__':
    game = Game(
        target=781,
        numbers=[10, 9, 3, 6, 8, 100],
    )

    print('Target', game.target)
    print('Numbers', ', '.join(str(number) for number in game.numbers))

    print(game.legal_actions())
    game.step(8)
    game.step(100)
    game.step(operator.mul)
    print('Raw', game.expression)
    print('Pretty', pretty_expression(game.expression))
    print(game.evaluated_expression)

    solve_brute_force(556, [50, 8, 3, 7, 2, 10])
    solve_brute_force_legal_only(556, [50, 8, 3, 7, 2, 10])

    unittest.main()

# print(game.legal_actions())
# game.step(game.legal_actions()[0])
# game.step(game.legal_actions()[0])
# game.step(game.legal_actions()[-1])
# print(game.expression)

# result = postfix_calculator(
#     [100, 25, operator.add, 5, operator.floordiv, 1, operator.sub])
# print(result)
