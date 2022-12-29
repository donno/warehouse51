// A work-in-progress solver for LYNE http://www.lynegame.com/
//
// TODO:
// - Make a web port.
// - OR add command line interface for providing the levels.
// - Actually write the solver part.

#include <algorithm>
#include <cctype>
#include <functional>
#include <tuple>
#include <iostream>
#include <memory>

typedef char piece_t;

namespace pieces
{
  // Represents a gate which requires two edges.
  static const piece_t GateTwo = '2';

  // Represents a gate which requires three edges.
  static const piece_t GateThree = '3';

  // Represents diamond pieces.
  static const piece_t Diamond = 'd';
  static const piece_t DiamondEnd = 'D';

  // Represents square pieces.
  static const piece_t Square = 's';
  static const piece_t SquareEnd = 'S';

  // Represents triangle pieces.
  static const piece_t Triangle = 't';
  static const piece_t TriangleEnd = 'T';
}

namespace svg
{
  const unsigned short spacing = 64;
  const unsigned short screenSize = 64;

  void drawCircle(
    std::ostream& output,
    unsigned short x,
    unsigned short y,
    unsigned short radius)
  {
    output << "        <circle cx=\"" << x << "\" cy=\"" << y << "\" r=\""
           << radius << "\" />" << std::endl;
  }

  void drawLine(
    std::ostream& output,
    unsigned short x1, unsigned short y1,
    unsigned short x2, unsigned short y2)
  {
    output
      << "        <line style=\"stroke: black\" x1=\"" << x1
      << "\" y1=\"" << y1 << "\" x2=\"" << x2  << "\" y2=\"" << y2 <<  "\" />"
      << std::endl;
  };
}

enum Direction {
  North,
  NorthEast,
  East,
  SouthEast,
  South,
  SouthWest,
  West,
  NorthWest
};

struct Level
{
  unsigned short width;
  unsigned short height;
  std::unique_ptr<piece_t[]> board;

  Level(unsigned short width, unsigned short height);

  piece_t& operator()(unsigned short x, unsigned short y);

  template <typename FUNCTION1, typename FUNCTION2>
  void as_svg(std::ostream& output,
              FUNCTION1 begin,
              FUNCTION2 end) const;


  // Returns true if two pieces can visit.
  //
  // The rules are as follows:
  //  - Triangles can only go to other triangles or gates.
  //  - Squares can only go to other squares or gates.
  //  - Diamonds can only go to other diamonds or gates.
  static bool can_visit(const piece_t lhs, const piece_t rhs);

  // Returns true if the peice at the given (x, y) coordinate can visit the
  // piece in the given direction.
  //
  // Returns false if there is no piece in the given direction.
  bool can_visit(unsigned short x, unsigned short y, Direction direction) const;
};

Level::Level(unsigned short width, unsigned short height)
: width(width),
  height(height),
  board(new piece_t[width * height])
{
}

piece_t& Level::operator()(unsigned short x, unsigned short y)
{
  return board[x + width * y];
}

template <typename FUNCTION1, typename FUNCTION2>
void Level::as_svg(std::ostream& output, FUNCTION1 begin, FUNCTION2 end) const
{
  using namespace svg;
  // SVG element.
  output << "<svg version=\"1.1\" baseProfile=\"full\"" << std::endl
         << "     xmlns=\"http://www.w3.org/2000/svg\"" << std::endl
         << "     xmlns:xlink=\"http://www.w3.org/1999/xlink\"" << std::endl
         << "     xmlns:ev=\"http://www.w3.org/2001/xml-events\">" << std::endl;

  begin(output);

  output << "    <g>" << std::endl;

  unsigned short yScreen = 32;
  for (unsigned short y = 0; y < height; ++y, yScreen += screenSize + spacing)
  {
    unsigned short xScreen = 32;
    for (unsigned short x = 0; x < width; ++x, xScreen += screenSize + spacing)
    {
      const piece_t piece = board[x + width * y];
      if (piece == pieces::Diamond || piece == pieces::DiamondEnd)
      {
        output
          << "        <polygon fill=\"orange\" points=\""
          << xScreen << ',' << (yScreen + screenSize / 2) << ' '
          << (xScreen + screenSize / 2)  << ',' << yScreen << ' '
          << (xScreen + screenSize) << ',' << (yScreen + screenSize / 2) << ' '
          << (xScreen + screenSize / 2) << ',' << yScreen + screenSize
          << "\" />" << std::endl;

        if (piece == pieces::DiamondEnd)
        {
          const auto screenQuater(screenSize / 4);
          output
            << "        <polygon style=\"fill: #815b3a\" points=\""
            << xScreen + screenQuater << ',' << (yScreen + screenSize / 2) << ' '
            << (xScreen + screenSize / 2)  << ',' << yScreen + screenQuater << ' '
            << (xScreen + screenSize - screenQuater)
            << ','
            << (yScreen + screenSize / 2)
            << ' '
            << (xScreen + screenSize / 2)
            << ','
            << yScreen + screenSize - screenQuater
            << "\" />" << std::endl;
        }
      }
      else if (piece == pieces::Triangle || piece == pieces::TriangleEnd)
      {
        output
          << "        <polygon fill=\"red\" points=\""
          << (xScreen + screenSize / 2)  << ',' << yScreen << ' '
          << xScreen << ',' << (yScreen + screenSize)  << ' '
          << (xScreen + screenSize) << ',' << (yScreen + screenSize)  << ' '
          << "\" />" << std::endl;
        if (piece == pieces::TriangleEnd)
        {
          const auto screenQuater(screenSize / 4);
          const auto triangleBottomY(yScreen + screenSize - screenSize / 6);
          output
            << "        <polygon style=\"fill: #ac707a\" points=\""
            << (xScreen + screenSize / 2)  << ',' << yScreen + screenQuater
            << ' '
            << xScreen + screenQuater << ',' << triangleBottomY << ' '
            << (xScreen + screenSize - screenQuater) << ',' << triangleBottomY
            << "\" />" << std::endl;
        }
      }
      else if (piece == pieces::Square || piece == pieces::SquareEnd)
      {
        output << "        <rect x=\"" << xScreen << "\" y=\"" << yScreen
               << "\" width=\"" << screenSize
               << "\" height=\"" << screenSize
               << "\"/>" << std::endl;

        if (piece == pieces::SquareEnd)
        {
          output << "        <rect x=\"" << (xScreen + screenSize / 4)
                 << "\" y=\"" << (yScreen + screenSize / 4)
                 << "\" width=\"" << screenSize / 2
                 << "\" height=\"" << screenSize / 2
                 << "\" style=\"fill: gray\"/>" << std::endl;
        }
      }
      else if (piece == pieces::GateTwo || piece == pieces::GateThree)
      {
        const unsigned screenSizeThird = screenSize / 3;
        const unsigned screenSizeTwoThirds = 2 * screenSize / 3 + 2;
        output
          << "        <polygon fill=\"green\" points=\""
          << (xScreen) << ',' << (yScreen + 1 * screenSizeThird) << ' '
          << (xScreen + screenSizeThird) << ',' << (yScreen) << ' '
          << (xScreen + screenSizeTwoThirds) << ',' << (yScreen) << ' '
          << (xScreen + screenSize) << ',' << (yScreen + screenSizeThird) << ' '
          << (xScreen + screenSize) << ',' << (yScreen + screenSizeTwoThirds) << ' '
          << (xScreen + screenSizeTwoThirds) << ',' << (yScreen + screenSize) << ' '
          << (xScreen + screenSizeThird) << ',' << (yScreen + screenSize) << ' '
          << (xScreen) << ',' << (yScreen + screenSizeTwoThirds) << ' '
          << "\" />" << std::endl;



        if (piece == pieces::GateTwo)
        {
          drawCircle(output, xScreen + screenSizeThird, yScreen + screenSize / 2,
                     screenSize / 8);
          drawCircle(output, xScreen + screenSize - screenSizeThird,
                     yScreen + screenSize / 2,
                     screenSize / 8);
        }
        else if (piece == pieces::GateThree)
        {
          drawCircle(output, xScreen + screenSize / 2,
                     yScreen + screenSize / 3,
                     screenSize / 8);
          drawCircle(output, xScreen + screenSizeThird,
                     yScreen + 2 * screenSize / 3,
                     screenSize / 8);
          drawCircle(output, xScreen + screenSize - screenSizeThird,
                     yScreen + 2 * screenSize / 3,
                     screenSize / 8);
        }
      }
    }
  }

  // Close the SVG element.
  output << "    </g>" << std::endl;

  end(output);

  output << "</svg>" << std::endl;
}

bool Level::can_visit(piece_t lhs, piece_t rhs)
{
  static_assert(pieces::TriangleEnd < pieces::Triangle,
                "The following checks rely on the fact the end should be less "
                "than non-end version.");
  std::tie(lhs, rhs) = std::minmax(lhs, rhs);
  // This ensures if lhs or rhs was an "end" then lhs is always the
  // end.
  return
    (lhs == rhs) ||
    (lhs == pieces::TriangleEnd && rhs == pieces::Triangle) ||
    (lhs == pieces::SquareEnd && rhs == pieces::Square) ||
    (lhs == pieces::DiamondEnd && rhs == pieces::Diamond) ||
    (lhs == pieces::GateTwo || rhs == pieces::GateTwo) ||
    (lhs == pieces::GateThree || rhs == pieces::GateThree);
};

bool Level::can_visit(unsigned short x, unsigned short y, Direction direction)
  const
{
  const piece_t current = board[x + width * y];
  switch (direction)
  {
  case North:
    return y > 0 && can_visit(current, board[x + width * (y - 1)]);
  case NorthEast:
    return y > 0 && x + 1 < width &&
      can_visit(current, board[x + 1 + width * (y - 1)]);
  case East:
    return x + 1 < width && can_visit(current, board[x + 1 + width * y]);
  case SouthEast:
    return y + 1 < height && x + 1 < width &&
      can_visit(current, board[x + 1 + width * (y + 1)]);
  case South:
    return y + 1 < height && can_visit(current, board[x + width * (y + 1)]);
  case SouthWest:
    return x > 0 && y + 1 < height &&
      can_visit(current, board[x - 1 + width * (y + 1)]);
  case West:
    return x > 0 && can_visit(current, board[x - 1 + width * y]);
  case NorthWest:
    return x > 0 && y > 0 && can_visit(current, board[x - 1 + width * (y - 1)]);
  }
  return false;
}

// Stores additional information for the solver.
struct SolverLevel
{
  unsigned short width;
  unsigned short height;
  const piece_t* const board;
  const piece_t* const boardEnd;
  // Directions bitfield.
  //
  // bit 0 = north,
  // bit 1 = north east,
  // bit 2 = east
  // bit 3 = south east,
  // bit 4 = south,
  // bit 5 = south west,
  // bit 6 = west,
  // bit 7 = north west,
  std::unique_ptr<unsigned int[]> directions;

  // level must be destructed after SolverLevel.
  SolverLevel(const Level& level);

  void as_svg(std::ostream&) const;

  // Determines what the current position can visit using the directions
  // bitfield computed on construction.
  bool can_visit(unsigned short x, unsigned short y, Direction direction) const;
};

SolverLevel::SolverLevel(const Level& level)
: width(level.width),
  height(level.height),
  board(level.board.get()),
  boardEnd(level.board.get() + level.width * level.height),
  directions(new unsigned int[level.width * level.height])
{
  std::fill(directions.get(), directions.get() + level.width * level.height, 0);
  // Direction rules:
  //  - Triangles can only go to other triangles or gates.
  //  - Squares can only go to other squares or gates.
  //  - Diamonds can only go to other diamonds or gates.
  //
  // These rules help reduce the search space for a solution.
  for (unsigned short y = 0, index = 0; y < height; ++y)
  {
    for (unsigned short x = 0; x < width; ++x, ++index)
    {
      if (level.can_visit(x, y, North))
      {
        directions[index] |= (1 << 0);
      }

      if (level.can_visit(x, y, NorthEast))
      {
        directions[index] |= (1 << 1);
      }

      if (level.can_visit(x, y, East))
      {
        directions[index] |= (1 << 2);
      }

      if (level.can_visit(x, y, SouthEast))
      {
        directions[index] |= (1 << 3);
      }

      if (level.can_visit(x, y, South))
      {
        directions[index] |= (1 << 4);
      }

      if (level.can_visit(x, y, SouthWest))
      {
        directions[index] |= (1 << 5);
      }

      if (level.can_visit(x, y, West))
      {
        directions[index] |= (1 << 6);
      }

      if (level.can_visit(x, y, NorthWest))
      {
        directions[index] |= (1 << 7);
      }
    }
  }
}

void SolverLevel::as_svg(std::ostream& output) const
{
  using namespace svg;
  const unsigned short halfScreenSize = screenSize / 2;
  const unsigned short next = screenSize + spacing;
  static_assert(screenSize == halfScreenSize + halfScreenSize,
                "Ensure screenSize is perfectly divisble by two.");

  // Directions.
  output << "    <g stroke=\"green\" >" << std::endl;

  // The solution should really be polylines, i.e lines from the ends of two
  // shapes, since they must be continous.
  unsigned short yScreen = 32 + halfScreenSize;
  for (unsigned short y = 0; y < height; ++y, yScreen += screenSize + spacing)
  {
    unsigned short xScreen = 32 + halfScreenSize;
    for (unsigned short x = 0; x < width; ++x, xScreen += screenSize + spacing)
    {
      // Go through each direction and determine which direction to draw.
      const auto direction = directions[x + y * width];

      // This could use
      if (can_visit(x, y, North))
      {
        drawLine(output, xScreen, yScreen, xScreen, yScreen - next);
      }
      if (can_visit(x, y, NorthEast))
      {
        drawLine(output, xScreen, yScreen, xScreen + next, yScreen - next);
      }
      if (can_visit(x, y, East))
      {
        drawLine(output, xScreen, yScreen, xScreen + next, yScreen);
      }
      if (can_visit(x, y, SouthEast))
      {
        drawLine(output, xScreen, yScreen, xScreen + next, yScreen + next);
      }
      if (can_visit(x, y, South))
      {
        drawLine(output, xScreen, yScreen, xScreen, yScreen + next);
      }
      if (can_visit(x, y, SouthWest))
      {
        drawLine(output, xScreen, yScreen, xScreen - next, yScreen + next);
      }
      if (can_visit(x, y, West))
      {
        drawLine(output, xScreen, yScreen, xScreen - next, yScreen);
      }
      if (can_visit(x, y, NorthWest))
      {
        drawLine(output, xScreen, yScreen, xScreen - next, yScreen - next);
      }
    }
  }
  output << "    </g>" << std::endl;
}

bool SolverLevel::can_visit(
  unsigned short x, unsigned short y, Direction direction) const
{
  switch (direction)
  {
  case North: return directions[x + width * y] & (1 << 0);
  case NorthEast: return directions[x + width * y] & (1 << 1);
  case East: return directions[x + width * y] & (1 << 2);
  case SouthEast: return directions[x + width * y] & (1 << 3);
  case South: return directions[x + width * y] & (1 << 4);
  case SouthWest: return directions[x + width * y] & (1 << 5);
  case West: return directions[x + width * y] & (1 << 6);
  case NorthWest: return directions[x + width * y] & (1 << 7);
  }
  return false;
}

void solve(const Level& level)
{
  // First step, determine all the possible directions for leaving each
  // cell/node/piece. This is handled by the constructor.
  SolverLevel solverableLevel(level);

  // Print out the current solution, at the start this will show all legal
  // moves between any two pieces.
  auto begin = [&](std::ostream& output) { solverableLevel.as_svg(output); };
  auto end = [](std::ostream& output) {};
  level.as_svg(std::cout, begin, end);

  // Other rules:
  //  - Ends must only have 1 edge.
  //  - Triangles, Squares and Diamonds can only be visited once, so must only
  //    have two edges (unless its an end which means it must have 1)
  //  - Gates must have N edges where N is the number of circles on the gate.

  // TODO: Provide a way to make copies of the solverable level so we can
  // evaluate removing paths to determine if it is a better solution.

  // Rules for finding a solution:
  // 1) Start at the ends, try to elimate ends with two edges.
  // --> Find ends with more than one edge.

  const auto isEndPiece = [](piece_t piece) { return std::isupper(piece); };

  for (auto current = solverableLevel.board;
       current != solverableLevel.boardEnd;
       current = std::find_if(current, solverableLevel.boardEnd, isEndPiece))
  {
    std::cerr << *current << std::endl;
    ++current;
  }
}

int main()
{
  using namespace pieces;

  Level lyne(4, 4);

  // TODO: Make an easier way to do this by allowing a row at a time to be
  // set.

  // The following is from http://thomasbowker.com/press/LYNE/images/lyne_04.png
  lyne(0, 0) = TriangleEnd;
  lyne(1, 0) = SquareEnd;
  lyne(2, 0) = DiamondEnd;
  lyne(3, 0) = Square;

  lyne(0, 1) = Diamond;
  lyne(1, 1) = Triangle;
  lyne(2, 1) = GateTwo;
  lyne(3, 1) = Square;

  lyne(0, 2) = Diamond;
  lyne(1, 2) = Diamond;
  lyne(2, 2) = GateThree;
  lyne(3, 2) = Square;

  lyne(0, 3) = DiamondEnd;
  lyne(1, 3) = SquareEnd;
  lyne(2, 3) = Triangle;
  lyne(3, 3) = TriangleEnd;

  solve(lyne);

  return 0;
}