#ifndef POSITION_HPP_
#define POSITION_HPP_

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

#include <iosfwd>

struct Position {
  const unsigned int x;
  const unsigned int y;

  Position(unsigned int x, unsigned int y);
  Position(const Position& position);
};

bool operator ==(const Position& lhs, const Position& rhs);
bool operator <(const Position& lhs, const Position& rhs);

const Position operator >>(std::istream& input, const Position&);
std::ostream& operator <<(std::ostream& input, const Position& position);

#endif
