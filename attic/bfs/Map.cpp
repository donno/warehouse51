//

#include "Map.hpp"

#include "Position.hpp"

#include <iostream>

Map::Map(unsigned int rows, unsigned int columns,
         std::vector<char>&& field,
         const Position& start, const Position& end)
: rows(rows),
  columns(columns),
  field(field),
  startPosition(start),
  endPosition(end)
{
}

bool Map::isValid(const Position& position) const{
  // The top left corner of a map is (1, 1) not (0, 0)
  if (position.x == 0) return false;
  else if (position.y == 0) return false;
  if (position.x == rows + 1 ) return false;
  else if (position.y == columns + 1) return false;

  return field[position.x - 1 + (position.y - 1) * rows] != 'X';
}

Map Map::read(std::istream& reader)
{
  unsigned int rows;
  unsigned int columns;

  reader >> rows;
  reader >> columns;

  const Position startPosition(reader >> Position(0,0));
  const Position endPosition(reader >> Position(0,0));

  std::vector<char> field;
  field.reserve(rows * columns);

  for (unsigned int row = 0; row < rows; ++row)
  {
    for (unsigned int column = 0; column < columns; ++column)
    {
      char cell;
      reader >> cell;
      field.push_back(cell);
    }
  }

  return Map(rows, columns, std::move(field), startPosition, endPosition);
}

std::ostream& operator <<(std::ostream& output, const Map& map)
{
  for (unsigned int row = 0; row < map.rows; ++row)
  {
    for (unsigned int column = 0; column < map.columns; ++column)
    {
      output << map.field[row + column * map.rows] << ' ';
    }
    output << std::endl;
  }
  return output;
}

