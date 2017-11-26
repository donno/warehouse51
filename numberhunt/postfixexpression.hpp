#ifndef NUMBER_HUNT_POSTFIX_EXPRESSION_H
#define NUMBER_HUNT_POSTFIX_EXPRESSION_H
//===----------------------------------------------------------------------===//
//
// NAME         : PostfixExpression
// SUMMARY      : Stores a Postfix expression
// COPYRIGHT    : (c) 2017 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
//
// Postfix notation or Reverse Polish notation is notation in mathematical
// where operands (numbers) appear before their operators (add, subtract, etc).
// For example, 5 6 + 2 -
//
// Infix expressions is the more common notation both taught and used where by
// the operators appear between the operators. For example, 5 + 6 - 2
//
// Usage:
//    const PostfixExpression expression(50, 10, '*', 8, 7, '*', '+');
//
//    // Evalutate the expression
//    std::cout << expression.Evaluate() << std::endl;
//
//===----------------------------------------------------------------------===//

#include <iosfwd>
#include <string>
#include <variant>
#include <vector>

enum class Operator : unsigned char
{
  Add = '+',
  Subtract = '-',
  Multiply = '*',
  Divide = '/',
};

class PostfixExpression
{
public:
  using operand_type = int;
  using operator_type = Operator;

  template<class ... Types>
  explicit PostfixExpression(Types ... Components);

  auto Count() const { return myItems.size(); }

  // Evalutate the first operator found in the expression (left to right).
  PostfixExpression EvaluateOnce() const;

  // Evalutate until there is only a sole value left.
  operand_type Evaluate() const;

  // Return the first value in the expression.
  //
  // If Count() is 1 then this is the result of the expression.
  operand_type FirstValue() const;

  // Converts the expression to inflix as a string.
  std::string ToInflixString() const;

private:
  static PostfixExpression EvaluateOnce(PostfixExpression Expression);

  // The Add() functions are called by the constructor.
  template<typename First, class ... Types>
  void Add(First FirstComponent, Types ... Components);

  void Add(char Operator);
  void Add(operand_type Operand);

  friend std::ostream&
  operator<<(std::ostream& os, const PostfixExpression& Expr);

  std::vector<std::variant<operand_type, operator_type>> myItems;
};

std::ostream& operator<<(std::ostream& os, const Operator& Operator);
std::ostream& operator<<(std::ostream& os, const PostfixExpression& Expr);

template<class ... Types>
PostfixExpression::PostfixExpression(Types ... Components)
{
  Add(Components...);
}

template<typename First, class ... Types>
void PostfixExpression::Add(First FirstComponent, Types ... Components)
{
  // I think there might be a better way to do this that doesn't invole a
  // recursive call using pack expansion syntax.
  Add(FirstComponent);
  Add(Components...);
}

#endif
