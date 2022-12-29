#ifndef MAP_HPP
#define MAP_HPP_

#include "Position.hpp"

#include <vector>

class Map
{
  Map(unsigned int rows, unsigned int columns, std::vector<char>&& field,
      const Position& start,
      const Position& end);

public:
  const unsigned int rows;
  const unsigned int columns;

  const std::vector<char> field;

  const Position startPosition;
  const Position endPosition;

  bool isValid(const Position& position) const;
  // Returns false if the position is outside of the map or there is an obstacle
  // at the postion, and true otherwise.

  static Map read(std::istream& reader);
};

std::ostream& operator <<(std::ostream& input, const Map& map);

#endif