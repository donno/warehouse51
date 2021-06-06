//===----------------------------------------------------------------------===
//
// NAME        : ExplosiveSweeper
// PURPOSE     : Provides minesweeper-like gameplay.
// COPYRIGHT   : (c) 2013 Sean Donnellan. All Rights Reserved.
// AUTHORS     : Sean Donnellan (darkdonno@gmail.com)
// STATUS      : Unfinished
// DESCRIPTION : Provides data structures to represent the grid in the
//               game of minesweeper.
//
//===----------------------------------------------------------------------===

#include <cstdlib>
#include <ctime>
#include <random>
#include <vector>

namespace
{
  namespace local
  {
    // A single square can have at most 8 mines around it.
    static const unsigned short Unknown = 9;
    static const unsigned short Mine = 10;

    class C_Grid
    {
    public:
      C_Grid(unsigned short Size);

      // Functions for looking up information about the grid.
      unsigned short Size() const { return mySize; }
      unsigned short operator [](unsigned short Index) const;

      // Function for playing on the grid.
      bool Pick(unsigned int X, unsigned int Y);
      // Returns true if there was a bomb at position (x,y)

      bool IsComplete() const;
      // Returns true if the board is complete, meaning only the mines remain.

    private:
      void Reset();

      void Open(unsigned int X, unsigned int Y);
      // Open up the area at Index.
      //
      // There should be no mine at Index.

      bool MineAt(unsigned short Index) const;
      unsigned short MinesNearby(unsigned int x, unsigned int y) const;

      std::vector<unsigned short> myGame;
      std::vector<unsigned short> myGrid;
      const unsigned short mySize;
      const unsigned short myMineCount;
    };
  }
}

local::C_Grid::C_Grid(unsigned short Size)
: myGrid(),
  mySize(Size),
  myMineCount(5)
{
  Reset();
}

#include <algorithm>
#include <iostream>

void local::C_Grid::Reset()
{
  myGame.clear();
  myGame.resize(mySize * mySize, Unknown);
  myGrid.clear();
  myGrid.resize(mySize * mySize, Unknown);

  // Insert the mines at the start of the list.
  std::fill_n(myGrid.data(), myMineCount, local::Mine);

  // Now shuffle the list.
  std::random_shuffle(myGrid.begin(), myGrid.end());

  // Determine the proximity of each cell to a mine.
  for (auto y = 0; y < mySize; ++y)
  {
    for (auto x = 0; x < mySize; ++x)
    {
      if (myGrid[x + y * mySize] != local::Mine)
      {
        myGrid[x + y * mySize] = MinesNearby(x, y);
      }
    }
  }
}

bool local::C_Grid::MineAt(unsigned short Index) const
{
  return myGrid[Index] == local::Mine;
}

unsigned short local::C_Grid::MinesNearby(unsigned int x, unsigned int y) const
{
  unsigned short minesNearby = 0;
  const unsigned int index = x + y * mySize;

  const bool firstRow = (y == 0);
  const bool lastRow = (y == mySize - 1);
  const bool firstColumn = (x == 0);
  const bool lastColumn = (x == mySize - 1);

  // The following order is tested, left, right, top, bottom.
  if (!firstColumn && MineAt(index-1)) ++minesNearby;
  if (!lastColumn && MineAt(index+1)) ++minesNearby;
  if (!firstRow && MineAt(index-mySize)) ++minesNearby;
  if (!lastRow && MineAt(index+mySize)) ++minesNearby;

  // Diagonals (top-left, top right.
  if (!firstRow)
  {
    // Test the top left and right corners.
    if (!firstColumn && MineAt(index-mySize-1)) ++minesNearby;
    if (!lastColumn && MineAt(index-mySize+1)) ++minesNearby;
  }

  if (!lastRow)
  {
    if (!firstColumn && MineAt(index+mySize-1)) ++minesNearby;
    if (!lastColumn && MineAt(index+mySize+1)) ++minesNearby;
  }

  return minesNearby;
}

unsigned short local::C_Grid::operator [](unsigned short Index) const
{
  return myGame[Index];
}

bool local::C_Grid::Pick(unsigned int X, unsigned int Y)
{
  // Transfer the number from myGrid to myGame.
  const auto index = X + Y * mySize;

  switch (myGrid[index])
  {
  case Mine:
    myGame[index] = myGrid[index];

    // It is now game over, so show the entry grid. This makes the above
    // statement redundant however it helps separate showign the title from
    // the game over view.
    myGame = myGrid;
    return true;
  case 0:
    // The square didn't have any numbers on it so go find all the
    // adjacent numbers to show.
    Open(X, Y);
    return false;
  default:
    myGame[index] = myGrid[index];
    return false;
  }
}

bool local::C_Grid::IsComplete() const
{
  // The number of unknowns should be equal to the mine counts. As if a mine
  // is revealed, its game over.
  return std::count(myGame.begin(), myGame.end(), local::Unknown) ==
    myMineCount;
}

void local::C_Grid::Open(unsigned int X, unsigned int Y)
{
  auto index = X + Y * mySize;
  if (myGame[index] != Unknown) return; // It has already been seen.
  myGame[index] = myGrid[index];

  if (myGrid[index] == 0)
  {
    const bool firstRow = (Y == 0);
    const bool lastRow = (Y == mySize - 1);
    const bool firstColumn = (X == 0);
    const bool lastColumn = (X == mySize - 1);

    // The following order is tested left, right, top, bottom.
    if (!firstColumn) Open(X-1, Y);
    if (!lastColumn) Open(X+1, Y);
    if (!firstRow) Open(X, Y-1);
    if (!lastRow) Open(X, Y+1);
  }
}

std::ostream& operator<<(std::ostream& Stream, const local::C_Grid& Grid)
{
  for (auto y = 0; y < Grid.Size(); ++y)
  {
    for (auto x = 0; x < Grid.Size(); ++x)
    {
      auto value = Grid[x + y * Grid.Size()];
      if (value == local::Mine) Stream << 'M';
      else if (value == local::Unknown) Stream << ' ';
      else Stream << value;
    }
    Stream << std::endl;
  }
  return Stream;
}

int main()
{

  // Small test to make sure the win condition works.
  {
    local::C_Grid grid(3);
    std::cout << grid << std::endl;
    std::cout << grid.IsComplete() << std::endl;
    grid.Pick(0, 0);
    grid.Pick(0, 2);
    grid.Pick(2, 0);
    grid.Pick(2, 1);
    std::cout << grid << std::endl;
    std::cout << grid.IsComplete() << std::endl;

    for (auto y = 0; y < grid.Size(); ++y)
    {
        grid.Pick(0, y);
        if (grid[y * grid.Size()] == 0)
        {
        break;
        }
    }
    std::cout << grid << std::endl;
    for (auto y = 0; y < grid.Size(); ++y)
    {
        grid.Pick(2, y);
    }
    std::cout << grid << std::endl;
  }

  local::C_Grid grid(3);

  unsigned short x, y;
  do
  {
    // Show the grid (field).
    std::cout << grid << std::endl;

    // Ask the user for the X (column) and Y (row) coordinate.
    std::cout << "Please provide the column and row to open: ";
    std::cin >> x >> y;

    // Perform the pick.
    if (grid.Pick(x, y))
    {
      // A mine was hit.
      std::cout << grid << std::endl;
      std::cout << "You hit a mine and lost the game." << std::endl;
      return 1;
    }
  } while (!grid.IsComplete());

  std::cout << "You cleared all the areas without mines, well done."
            << std::endl;
  return 0;
}
