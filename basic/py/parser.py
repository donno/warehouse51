"""Parses a stream of characters into tokens (lexeme) for a BASIC language.

Copyright (C) 2019 Sean Donnellan.
SPDX-License-Identifier: MIT
"""
import enum
import functools
import string

class LexemeType(enum.Enum):
    Unknown = 0
    Integer = 1
    IntegerBase16 = 2
    Real = 3
    String = 4
    Identifier = 5
    Symbol = 6
    Comment = 7

class Integer:
    def __init__(self, value, base=10):
        self.value = value
        self.base = base

    def __str__(self):
        return 'Integer(%d)' % self.value

class Real:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'Real(%f)' % self.value

class Identifier:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return 'Identifier(%s)' % self.value

class String:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return '"%s"' % self.value

class Comment:
    def __init__(self, value):
        self.value = value

class Symbol:
    Tokens = ('=', '+', '-', '*', '/', '(', ')', ';', ',', ':', '.', '>', '<')

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

def parse(reader):
    lexeme_type = LexemeType.Unknown
    tokens = []

    def _terminate():
        if lexeme_type == LexemeType.Comment:
            return Comment(''.join(tokens))
        elif lexeme_type == LexemeType.Integer:
            value = int(''.join(tokens))
            return Integer(value)
        elif lexeme_type == LexemeType.IntegerBase16:
            value = int(''.join(tokens), 16)
            return Integer(value, base=16)
        if lexeme_type == LexemeType.Real:
            value = float(''.join(tokens))
            return Real(value)
        elif lexeme_type == LexemeType.Identifier:
            return Identifier(''.join(tokens))
        elif lexeme_type == LexemeType.Symbol:
            return Symbol(''.join(tokens))
        elif lexeme_type == LexemeType.String:
            return String(''.join(tokens))
        else:
            raise ValueError('Can not terminate %s' % lexeme_type)

    for ch in iter(functools.partial(reader.read, 1), ''):
        if lexeme_type == LexemeType.Unknown:
            # Try to figure out the type.
            if ch == '&':
                lexeme_type = LexemeType.IntegerBase16
                tokens = []
            elif ch.isdigit():
                # Integer or real, lets assume integer until proven otherwise
                lexeme_type = LexemeType.Integer
                tokens.append(ch)
            elif ch.isalpha():
                lexeme_type = LexemeType.Identifier
                tokens.append(ch)
            elif ch in Symbol.Tokens:
                lexeme_type = LexemeType.Symbol
                tokens.append(ch)
            elif ch == "'":
                lexeme_type = LexemeType.Comment
                tokens = []
            elif ch == '"':
                lexeme_type = LexemeType.String
                tokens = []
            elif ch.isspace():
                continue
            else:
                raise NotImplementedError('Unknown char "%s"' % ch)
        elif lexeme_type == LexemeType.Integer:
            if ch.isdigit():
                tokens.append(ch)
            elif ch.isspace():
                yield _terminate()

                lexeme_type = LexemeType.Unknown
                tokens = []
            elif ch in Symbol.Tokens:
                yield _terminate()

                lexeme_type = LexemeType.Symbol
                tokens = [ch]
            elif ch == '.':
                lexeme_type = LexemeType.Real
                tokens.append(ch)
            else:
                # If this is a . then we go from Integer to Real.
                raise NotImplementedError('Unknown char "%s"' % ch)
        elif lexeme_type == LexemeType.IntegerBase16:
            if not tokens:
                if ch in string.hexdigits:
                    tokens.append(ch)
                elif ch == 'H':
                    pass
                else:
                    raise ValueError('Expected & followed by H got %s', ch)
            elif ch in string.hexdigits:
                tokens.append(ch)
            elif ch.isspace():
                yield _terminate()

                lexeme_type = LexemeType.Unknown
                tokens = []
            else:
                raise NotImplementedError('Unknown char "%s"' % ch)
        elif lexeme_type == LexemeType.Real:
            if ch.isdigit():
                tokens.append(ch)
            elif ch.isspace():
                yield _terminate()

                lexeme_type = LexemeType.Unknown
                tokens = []
            elif ch in Symbol.Tokens:
                yield _terminate()

                lexeme_type = LexemeType.Symbol
                tokens = [ch]
            else:
                raise NotImplementedError('Unknown char "%s" for %s' % (ch, lexeme_type))
        elif lexeme_type == LexemeType.Identifier:
            if ch.isalpha() or ch.isdigit():
                tokens.append(ch)
            elif ch.isspace():
                yield _terminate()

                lexeme_type = LexemeType.Unknown
                tokens = []
            elif ch in ('$', '%', '#'):
                # Sigils on the end of variable name that mean types in
                # QBasic. Where $ means string, % means integer, & means long,
                # ! is float and # is float.
                tokens.append(ch)
            elif ch in Symbol.Tokens:
                yield _terminate()

                # Start the next one.
                lexeme_type = LexemeType.Symbol
                tokens = [ch]
            else:
                raise NotImplementedError('Unknown char "%s" for %s (%s)' % (ch, lexeme_type, tokens))
        elif lexeme_type == LexemeType.Symbol:
            if ch.isspace():
                yield _terminate()

                lexeme_type = LexemeType.Unknown
                tokens = []
            elif ch.isdigit():
                yield _terminate()

                lexeme_type = LexemeType.Integer
                tokens = [ch]
            elif ch == '"':
                yield _terminate()

                lexeme_type = LexemeType.String
                tokens = []
            elif ch.isalpha():
                yield _terminate()

                lexeme_type = LexemeType.Identifier
                tokens = [ch]
            elif ch in Symbol.Tokens:
                yield _terminate()

                lexeme_type = LexemeType.Symbol
                tokens = [ch]
            else:
                raise NotImplementedError('Unknown char "%s" for %s (%s)' % (ch, lexeme_type, tokens))
        elif lexeme_type == LexemeType.String:
            if ch == '"':
                yield _terminate()

                lexeme_type = LexemeType.Unknown
                tokens = []
            else:
                tokens.append(ch)
        elif lexeme_type == LexemeType.Comment:
            if ch == '\n':
                yield _terminate()

                lexeme_type = LexemeType.Unknown
                tokens = []
            else:
                tokens.append(ch)
        else:
            raise NotImplementedError('Unknown char "%s" for %s' % (ch, lexeme_type))

    if lexeme_type != LexemeType.Unknown:
        yield _terminate()

if __name__ == '__main__':
    with open('lexer_example.bas') as reader:
        for token in parse(reader):
            print(token)
