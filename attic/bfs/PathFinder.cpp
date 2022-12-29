//===----------------------------------------------------------------------===//
//
// NAME         : PathFinder
// PURPOSE      : Finding a path through a two dimensional map.
// COPYRIGHT    : (c) 2011 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides a class which performs breadth first search to find
//                a path through a map.
//
//===----------------------------------------------------------------------===//

#include "Position.hpp"
#include "Map.hpp"

#include <set>
#include <queue>

#include <algorithm>
#include <fstream>
#include <string>
#include <iostream>
#include <vector>

// Defintions.

struct Node
{
  const Position position;
  std::vector<Position> path; // The path travelled so far to get to position.

  Node(const Position& position, const std::vector<Position>& path)
  : position(position), path(path) {}
};


class PathFinder
{
  const Map& map;
  // The map in which the path will be found on.

  std::queue<Node> frontier;
  // Keeps track of the places to visit.

  std::set<Position> visited;
  // Keep track of all the positions already visited.

  void add(const Position& position, const std::vector<Position>& path);
  // Adds a position to the frontier provided its a valid position on the map.
  // The path is the positions it moved to get to position.

  PathFinder(const Map& map);

public:
  static std::vector<Position> findPath(const Map& map);
  // Finds a path from the starting position to the end position on the provided
  // map.
};


struct Vector
{
  const int dx;
  const int dy;

  Vector(int dx, int dy) : dx(dx), dy(dy) {}
};

Position operator +(const Position& lhs, const Vector& rhs);

// Implementation.

void PathFinder::add(
  const Position& position,
  const std::vector<Position>& path)
{
  if (!map.isValid(position)) return;

  if (visited.find(position) == visited.end())
  {
    frontier.push(Node(position, path));
    visited.insert(position); // Not sure about this one.
  }
}

PathFinder::PathFinder(const Map& map) : map(map) {}

std::vector<Position> PathFinder::findPath(const Map& map)
{
  PathFinder pathFinder(map);
  std::queue<Node>& frontier = pathFinder.frontier;

  // Start off at the starting position.
  pathFinder.add(map.startPosition, std::vector<Position>());

  for ( ; !frontier.empty(); frontier.pop())
  {
    const Node& node = frontier.front();
    const Position& position = node.position;

    // Has the end position been reached?
    if (position == map.endPosition)
    {
      std::cout << "Solution found" << std::endl;
      return node.path;
    }

    // position has now been visited so add it to the list..
    pathFinder.visited.insert(position);

    std::vector<Position> path(node.path);
    path.push_back(position);

    // Populate frontier with new elements.
    pathFinder.add(position + Vector(0, 1), path);  // Move up
    pathFinder.add(position + Vector(0, -1), path); // Move down
    pathFinder.add(position + Vector(-1, 0), path); // Move left
    pathFinder.add(position + Vector(1, 0), path);  // Move right
  }

  // Consider throwing an exception here...
  std::cout << "No solution found" << std::endl;
  return std::vector<Position>();
}

Position operator +(const Position& lhs, const Vector& rhs)
{
  return Position(lhs.x + rhs.dx, lhs.y + rhs.dy);
}

void PrintUsage(const char* program)
{
  std::cout << "Usage: " << program << " -m <map> [-s <algorithm>] "
            << std::endl << std::endl
            << "If algorithm is not specified then bfs will be used."
            << std::endl;
}

int main(int argc, char* argv[])
{
  if (argc < 2)
  {
    PrintUsage(argv[0]);
    return 0;
  }

  // Process arguments
  std::string filename;
  std::string algorithm("bfs");
  for (int i = 1; i < argc; ++i)
  {
    if (argv[i] == std::string("-m"))
    {
      ++i;
      if (i >= argc)
      {
        std::cerr << "error: -m option should have the filename after it." 
                  << std::endl;
        return 1;
      }
      else
      {
        filename = argv[i];
      }
    }
    else if (argv[i] == std::string("-s"))
    {
      ++i;
      if (i >= argc)
      {
        std::cerr << "error: -s option should have the name of the algorithm "
                  << "after it." << std::endl;
        return 1;
      }
      else
      {
        algorithm = argv[i];
        std::transform(algorithm.begin(), algorithm.end(),
                       algorithm.begin(), ::tolower);

        if (algorithm != "bfs" && algorithm != "ucs" && algorithm != "astar")
        {
          std::cerr << "error: -s option should be one of bfs, ucs or astar "
                    << "not " << algorithm << std::endl;
          return 1;
        }
      }
    }
  }

  if (filename.empty())
  {
    PrintUsage(argv[0]);
    return 1;
  }

  std::cout << algorithm << std::endl;

  std::ifstream file(filename, std::ifstream::in);

  const Map map = Map::read(file);

  std::cout << "Map (" << filename << "): "
            << map.rows << " by "<< map.columns << std::endl;
  std::cout << "Starting position: " << map.startPosition << std::endl;
  std::cout << "End position: " << map.endPosition << std::endl;
  std::cout << map;

  const std::vector<Position> path = PathFinder::findPath(map);

  if (!path.empty())
  {
    std::cout << "Path from start to end: ";
    for (std::vector<Position>::const_iterator position = path.begin();
         position != path.end();
         ++position)
    {
      std::cout << *position << " -> ";
    }
    std::cout << map.endPosition << std::endl;
    std::cout << std::endl;
  }
  else if (map.startPosition == map.endPosition)
  {
    std::cout << "No need to move as the start is the end." << std::endl;
  }


  return 0;
}
