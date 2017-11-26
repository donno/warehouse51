//===----------------------------------------------------------------------===//
//
// NAME         : PostfixExpression
// SUMMARY      : Stores a Postfix expression
// COPYRIGHT    : (c) 2017 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
//
//===----------------------------------------------------------------------===//

#include "postfixexpression.hpp"

#include <algorithm>
#include <iostream>
#include <type_traits>

namespace
{
    namespace local
    {
        using variant_type = std::variant<PostfixExpression::operand_type,
                                        PostfixExpression::operator_type>;

        bool IsOperator(const variant_type &Item);

        PostfixExpression::operand_type Evaluate(
            PostfixExpression::operator_type,
            PostfixExpression::operand_type,
            PostfixExpression::operand_type);
    }
}

bool local::IsOperator(const variant_type &Item)
{
    return std::holds_alternative<PostfixExpression::operator_type>(Item);
}

PostfixExpression::operand_type local::Evaluate(
    PostfixExpression::operator_type Operator,
    PostfixExpression::operand_type Operand1,
    PostfixExpression::operand_type Operand2)
{
    using operator_type = PostfixExpression::operator_type;
    switch (Operator)
    {
    case operator_type::Add:
        return Operand1 + Operand2;
    case operator_type::Subtract:
        return Operand1 - Operand2;
    case operator_type::Divide:
        return Operand1 / Operand2;
    case operator_type::Multiply:
        return Operand1 * Operand2;
    }

    std::terminate();
}

PostfixExpression PostfixExpression::EvaluateOnce() const
{
    return EvaluateOnce(*this);
}

PostfixExpression::operand_type PostfixExpression::Evaluate() const
{
    auto next = *this;
    while (next.Count() > 1)
    {
        next = next.EvaluateOnce();
    }
    return next.FirstValue();
}

PostfixExpression::operand_type PostfixExpression::FirstValue() const
{
    return std::get<PostfixExpression::operand_type>(myItems.front());
}

PostfixExpression
PostfixExpression::EvaluateOnce(PostfixExpression Expression)
{
    // Find the first operator in the expression.
    const auto firstOperator =
        std::find_if(Expression.myItems.begin(),
                     Expression.myItems.end(),
                     local::IsOperator);

    if (firstOperator == Expression.myItems.cend())
    {
        // Error
        std::terminate();
    }

    auto operator_ = std::get<operator_type>(*firstOperator);
    auto operand_2 = std::get<operand_type>(*std::prev(firstOperator, 1));
    auto operand_1 = std::get<operand_type>(*std::prev(firstOperator, 2));

    // Evalutate and then replace the operator with the value
    *firstOperator = local::Evaluate(operator_, operand_2, operand_1);

    // Remove the operands.
    Expression.myItems.erase(std::prev(firstOperator, 2), firstOperator);

    // At this point, what was done is the the previous two operands and the
    // operator have been replaced with the value.
    return Expression;
}

void PostfixExpression::Add(operand_type Operand)
{
    myItems.push_back(Operand);
}

void PostfixExpression::Add(char Operator)
{
    switch (Operator)
    {
    case '+':
        myItems.emplace_back(Operator::Add);
        break;
    case '-':
        myItems.emplace_back(Operator::Subtract);
        break;
    case '*':
        myItems.emplace_back(Operator::Multiply);
        break;
    case '/':
        myItems.emplace_back(Operator::Divide);
        break;
    }
}

std::ostream &operator<<(std::ostream &os, const PostfixExpression &Expr)
{
    os << "Expression [ ";
    for (const auto &item : Expr.myItems)
    {
        std::visit([&os](auto &&arg) {
            using T = std::decay_t<decltype(arg)>;
            static_assert(std::is_same_v<T, PostfixExpression::operand_type> ||
                              std::is_same_v<T, PostfixExpression::operator_type>,
                          "Only expected these two types.");
            os << arg << ' ';
        },
                   item);
    }
    os << "]";
    return os;
}

std::ostream &operator<<(std::ostream &os, const Operator &Operator)
{
    os << static_cast<unsigned char>(Operator);
    return os;
}

//===--------------------------- End of the file --------------------------===//