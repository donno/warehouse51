// Generate level.
//
// Concepts:
// - Hallways - These connect together rooms, just large enough for the player to fit.
// - Rooms - a space where the player can move around.
// - Entrance (staircase going to the level above, this is where they entered the level from. 
// - Exit (staircase going to the level below, this is generally the objective to go deeper
//         into the dungeon)
// Variables:
//   The following aspects can control the generation of a room.
//   - Map size (width and height).
//   - Room size (min/max) and (width and height).
//
//
// Inspiration:
//  http://www.roguebasin.com/index.php?title=Dungeon-Building_Algorithm
//  http://www.roguebasin.com/index.php?title=RNG
//  http://www.odedwelgreen.com/karcero/
//  http://gamasutra.com/blogs/AAdonaac/20150903/252889/Procedural_Dungeon_Generation_Algorithm.php
//  https://en.wikipedia.org/wiki/Flood_fill

#include <memory>
#include <cstdint>

struct Extent1D
{
std::uint16_t lower;
std::uint16_t upper;
};

struct Extent2D
{
    Extent1D width;
    Extent1D height;
};

struct Rect2D
{
    std::uint16_t width;
    std::uint16_t height;
};

enum RoomCount
{
    None, // Hallways only
    Few,
    Some,
    Many,
};

enum Tile : char
{
    Void = '#',
    Floor = ' ',
    Door = 'D',
};

// This controls the amount of empty space over the total map.
// For example, Sparse means there is lots of empty space between
// hallways and rooms, where dense there is typically only a single
// gap between hallways/rooms, when combined with "few rooms", it
// menas there will be lots of hallways.
enum Sparseness
{
};

struct Level
{
    std::unique_ptr<Tile[]> tiles;
    Rect2D dimensions;

    Level(const Rect2D& Dimensions);
};

Level::Level(const Rect2D& Dimensions)
: tiles(new Tile[Dimensions.width * Dimensions.height]),
dimensions(Dimensions)
{
    std::fill_n(tiles.get(), Dimensions.width * Dimensions.height, Void);
}

#include <iostream>

std::ostream& operator<<(std::ostream& output, const Level& level)
{
    const auto width = level.dimensions.width;
    for (std::uint16_t row = 0; row < level.dimensions.height; ++row)
    {
        for (std::uint16_t column = 0; column < width; ++column)
        {
            std::cout << static_cast<char>(level.tiles[column + row * width]);
        }
        std::cout << std::endl;
    }
    return output;
}

void GenerateRooms(
Level* level,
const Extent2D& RoomExtents,
RoomCount RoomCount)
{
// Based on the size of the level, decide how many rooms could fit.

}


int main()
{
    // Some generation properties.
    Extent2D room;
    room.width = { 2, 5 };
    room.height = { 2, 5 };
    
    Level level({60, 20});
GenerateRooms(&level, room, Many);
    std::cout << level << std::endl;
    
    return 0;
}

// e:\Programs\VisualStudio14.0\VC\vcvarsall.bat