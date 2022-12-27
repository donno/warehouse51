"""Create polyhedron from notation

This is based on polyhedron-building operators.

Status: Very very early days.
"""


class Base:
    """Represents a base type."""
    type_code_to_name = {
        'T': 'tetrahedron',
        'C': 'cube',
        'O': 'octahedron',
        'I': 'icosahedron',
        'D': 'dodecahedron',
    }

    type_codes = set(type_code_to_name.keys())

    def __init__(self, type_code):
        self.type_code = type_code

    def __repr__(self) -> str:
        return f'Base(\'{self.type_code}\')'

    def __str__(self) -> str:
        return self.type_code

    @property
    def name(self) -> str:
        return self.type_code_to_name[self.type_code]


class BaseWithN:
    """Represents a base type with a N value. For example a n-sided prism or
    the Nth Johnson solids.

    For more about Johnson solids read:
        https://en.wikipedia.org/wiki/List_of_Johnson_solids
    """
    type_code_to_name = {
        'P': 'prism',
        'A': 'antiprism',
        'Y': 'pyramid',  # n-sided pyramid
        'J': 'johnson',  # N should be 1 to 92
        'U': 'cupola',
        'V': 'anticupola',
    }

    type_codes = set(type_code_to_name.keys())

    def __init__(self, type_code, n):
        self.type_code = type_code
        self.n = n

    def __repr__(self) -> str:
        return f'BaseWithN(\'{self.type_code}\', {self.n})'

    def __str__(self) -> str:
        return self.type_code + str(self.n)

    @property
    def name(self) -> str:
        return self.type_code_to_name[self.type_code] + ' ' + str(self.n)


class Operation:
    op_code_to_name = {
        'd': 'dual',
        'a': 'ambo',
        'k': 'kisN',
        'g': 'gyro',
        'p': 'propellor',
        'r': 'reflect',
        'c': 'chamfer',
        'w': 'whirl',
        'n': 'insetN',
        'x': 'extrudeN',
        'l': 'loft',
        'P': 'perspectiva1',
        'q': 'quinto',
        'u': 'trisub',
        'H': 'hollow',
        'Z': 'triangulate',
        'C': 'canonicalize',
        'A': 'adjustXYZ',
    }

    def __init__(self, op_code, operand: int = None):
        self.op_code = op_code
        self.operand = operand

    def __repr__(self) -> str:
        return f'Operation(\'{self.op_code}\')'

    def __str__(self) -> str:
        return self.op_code

    @property
    def name(self) -> str:
        if self.operand:
            return self.op_code_to_name[self.op_code] + f' {self.operand}'
        return self.op_code_to_name[self.op_code]


def parse_recipe(recipe):
    """Parse a recipe for a polyhedral."""
    def token_operator(characters):
        n_or_op = next(characters)
        if n_or_op.isdigit():
            n = n_or_op
            n_or_op = next(characters)
            if n_or_op.isdigit():
                n = int(n_or_op) * 10 + int(n)
                n_or_op = next(characters)  # Handles C40
        else:
            n = None

        op_code = n_or_op
        if op_code not in Operation.op_code_to_name:
            raise ValueError(
                f'Invalid operation {op_code} must be one of ' +
                f'{set(Operation.op_code_to_name.keys())}.')

        return Operation(op_code, n)

    def token_base(characters):
        n_or_type = next(characters)
        if n_or_type.isdigit():
            # Assume its an argument until we can check the next.
            base_type = next(characters)
            if base_type not in BaseWithN.type_codes:
                raise ValueError(
                    f'Base type was {base_type} but a argument was given and '
                    f'only {BaseWithN.type_codes} may have one.')

            return BaseWithN(base_type, n_or_type)
        else:
            if n_or_type not in Base.type_codes:
                raise ValueError(
                    f'Base type was {n_or_type} but must be one of given base '
                    f'types {Base.type_codes ^ BaseWithN.type_codes}.')
            return Base(n_or_type)

    characters = reversed(recipe)
    base = token_base(characters)
    operators = []
    while True:
        try:
            operator = token_operator(characters)
        except StopIteration:
            break
        operators.append(operator)

    return base, operators


if __name__ == '__main__':
    # https://levskaya.github.io/polyhedronisme/?recipe=kn4C40A0dA4
    base, operators = parse_recipe("kn4C40A0dA4")
    print(base.name + ': ' + ', '.join(op.name for op in operators))

