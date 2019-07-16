#ifndef BASIC_LEXER_HPP
#define BASIC_LEXER_HPP
//===----------------------------------------------------------------------===//
//
// Performs lexical analysis on an input stream. The lexical grammar followed
// is that of a variant of the BASIC family of programming languages.
//
// Lexemes for BASIC are as follows:
// - Integer    (\d+)
// - Real       (\d+\.\d+)
// - Identifier ([a-zA-Z][a-zA-Z0-9]+[$%#]?)
// - String     "([^"]*)
// - Comment    '.* (till end of line.)
// - Symbol     One of ()*+',-./:;<=>
//
// Copyright (C) 2019 Sean Donnellan.
// SPDX-License-Identifier: MIT
//
//===----------------------------------------------------------------------===//

#include <istream>
#include <variant>
#include <vector>

namespace basic::lexer
{
    struct Identifier
    {
        std::string myName;
    };

    struct Comment
    {
        std::string myComment;
    };

    struct Symbol
    {
        char mySymbol;
    };

    using Token = std::variant<
        Comment,
        int, // Integer constant
        float, // Float (Real) constant
        Identifier, // Variable or label name
        std::string, // String literal
        Symbol>;

    Token parse(std::istream& input);
    std::vector<Token> parse_all(std::istream& input);
}

#endif
