//===----------------------------------------------------------------------===//
//
// Copyright (C) 2019 Sean Donnellan.
// SPDX-License-Identifier: MIT
//
//===----------------------------------------------------------------------===//

#include "parser.hpp"

#include <algorithm>
#include <cassert>
#include <cstdio>

static basic::parser::Token parse_identifier(std::istream& input, char first);
static basic::parser::Token parse_integer(std::istream& input, char first);
static basic::parser::Token parse_integer_base_16(std::istream& input);
static basic::parser::Token parse_string(std::istream& input);

basic::parser::Token parse_identifier(std::istream& input, char first)
{
    // This also supports sigils on the end of variable name that imply the
    // type of variables in QBasic.
    auto is_acceptable = [](char c)
    {
        return std::isdigit(c) || std::isalpha(c) ||
            c == '$' || // Name is a string.
            c == '%' || // Name is a integer.
            c == '#'; // Name is a a long
    };

    std::string tokens(1, first);
    for (char c = input.peek(); is_acceptable(c); c = input.peek())
    {
        tokens.push_back(input.get());
    }
    return basic::parser::Identifier{tokens};
}

basic::parser::Token parse_integer(std::istream& input, char first)
{
    std::string tokens(1, first);
    for (char c = input.peek(); std::isdigit(c); c = input.peek())
    {
        tokens.push_back(input.get());
    }
    return {std::stoi(tokens)};
}

basic::parser::Token parse_integer_base_16(std::istream& input)
{
    const char hex = input.peek();
    assert(hex == 'H'); // TODO: THis should probably throw an error.
    input.get();

    std::string tokens;
    for (char c = input.peek(); std::isxdigit(c); c = input.peek())
    {
        tokens.push_back(input.get());
    }
    return {std::stoi(tokens, 0, 16)};
}

basic::parser::Token parse_string(std::istream& input)
{
    // TODO: Handle escaping of the ".
    std::string value;
    for (char c = input.peek(); c != '"' && !input.eof(); c = input.peek())
    {
        value.push_back(input.get());
    }

    if (!input.eof()) assert(input.peek() == '"');

    input.get(); // Remove the " from the input.

    return value;
}

basic::parser::Token basic::parser::parse(std::istream& input)
{
    constexpr char sorted_symbols[] = {
        '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>',
    };

    auto c = input.get();
    while (std::isspace(c)) c = input.get();
    if (std::isdigit(c))
    {
        return parse_integer(input, static_cast<char>(c));
    }
    else if (c == '&')
    {
        return parse_integer_base_16(input);
    }
    else if (std::isalpha(c))
    {
        return parse_identifier(input, c);
    }
    else if (std::binary_search(std::begin(sorted_symbols),
                                std::end(sorted_symbols),
                                c))
    {
        return Symbol{static_cast<char>(c)};
    }
    else if (c == '"')
    {
        return parse_string(input);
    }
    else if (c == '\'')
    {
        Comment comment;
        std::getline(input, comment.myComment);
        return comment;
    }
    else if (std::isspace(c))
    {
        return {};
    }
    else
    {
        std::printf("Next token was: %c\n", c);
    }

    return {};
}

std::vector<basic::parser::Token> basic::parser::parse_all(
    std::istream& input)
{
    std::vector<Token> tokens;
    while (!input.eof()) tokens.push_back(parse(input));
    return tokens;
}

// Main

#include <fstream>
#include <iostream>

int main(int argc, const char* argv[])
{
    if (argc != 2)
    {
        std::cerr << "usage: " << argv[0] << " file.bas" << std::endl;
        return 1;
    }

    using namespace basic::parser;

    std::fstream s(argv[1], std::fstream::in);
    for (const auto& token : parse_all(s))
    {
        std::visit([](auto&& arg)
        {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, Comment>)
                std::cout << "Comment with value " << arg.myComment << '\n';
            else if constexpr (std::is_same_v<T, float>)
                std::cout << "Real/Float with value " << arg << '\n';
            else if constexpr (std::is_same_v<T, int>)
                std::cout << "Integer with value " << arg << '\n';
            else if constexpr (std::is_same_v<T, Identifier>)
                std::cout << "Identifier with value " << arg.myName << '\n';
            else if constexpr (std::is_same_v<T, Symbol>)
                std::cout << "Symbol with value " << arg.mySymbol << '\n';
            else if constexpr (std::is_same_v<T, std::string>)
                std::cout << "String with value " << arg << '\n';
        }, token);
    }

    return 0;
}
