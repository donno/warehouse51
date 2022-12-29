//===----------------------------------------------------------------------===//
//
// NAME         : Position
// PURPOSE      : Represents a position in 2D space.
// COPYRIGHT    : (c) 2011 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides a class which represents a point in 2D space where
//                the x and y is >= 0 and instances of the class are immutable.
//
//===----------------------------------------------------------------------===//

#include "Position.hpp"

#include <iostream>

Position::Position(unsigned int x, unsigned int y)
: x(x), y(y)
{
}

Position::Position(const Position& position)
: x(position.x), y(position.y)
{
}

bool operator ==(const Position& lhs, const Position& rhs)
{
  return lhs.x == rhs.x && lhs.y == rhs.y;
}

bool operator <(const Position& lhs, const Position& rhs)
{
  return (lhs.x < rhs.x) || ((lhs.x == rhs.x) && (lhs.y < rhs.y));
}

std::ostream& operator <<(std::ostream& input, const Position& position)
{
  input << '(' << position.x << ", " << position.y << ')';
  return input;
}

const Position operator >>(std::istream& input, const Position&)
{
  unsigned int x, y;
  input >> x;
  input >> y;

  return Position(x, y);
}
