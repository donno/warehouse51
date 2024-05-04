//===----------------------------------------------------------------------===//
//
// NAME         : HGT
// SUMMARY      : Provides functions for working with HGT files.
// COPYRIGHT    : (c) 2020 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Details of the format are from the quick start documentation.
//         https://dds.cr.usgs.gov/srtm/version2_1/Documentation/Quickstart.pdf
//
// The filename refers to the latitude and longitude of the lower left corner
// of the tile and is the geometric centre of that lower left pixel.
//
// The contents of the file are a series of signed two-byte integers in
// big-endian order.
//
// A cell (or pixel as mentioned above) that has no data is known as data
// voids (i.e heights) and have a value of -32768.
//
// Heights are in meters referenced to the WGS84/EGM96 geoid.
//
// Compiling: (MSVC) cl /EHsc /std:c++17 /nologo /DWITH_HGT_MAIN hgt.cpp
//                   clang++ -std=c++20 -DWITH_HGT_MAIN hgt.cpp
//                   g++-11 -std=c++20 -DWITH_HGT_MAIN hgt.cpp
//===----------------------------------------------------------------------===//

#include "hgt.hpp"

#include <cctype>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>

#include <stdlib.h>

namespace
{
    namespace local
    {
        // Name is expected to start with the cardial (E/e or W/w).
        float ParseLongitude(const char* Name);

        // If true then the entire file will be loaded into memory.
        // This is 3601 * 3601 * 2 bytes (~25MB) for a SRTM1 and 1201 * 1201 *
        // 2 bytes (~3MB). Keep in mind the effects of this if doing this in
        // parallel.
        constexpr bool UseSingleReadCall = true;

        // If true then ForEachHeightWithIndex() will simply use a suitable
        // lambda with ForEachHeigh() instead.
        constexpr bool UseLambdaForIndex = true;
    }
}

float local::ParseLongitude(const char* Name)
{
    const bool isEasting = *Name == 'E' || *Name == 'e';
    const bool isWesting = *Name == 'W' || *Name == 'w';
    if (!isEasting && !isWesting)
    {
        throw std::runtime_error("Filename of HGT file in wrong format should "
                                 "contain W(esting) or E(easting).");
    }

    if (std::isdigit(Name[1]) && std::isdigit(Name[2]) &&
        std::isdigit(Name[3]))
    {
        float longitude;
        if (auto [next, ec] = std::from_chars(Name + 1, Name + 4, longitude);
            ec == std::errc())
        {
            return isEasting ? longitude :  -longitude;
        }
        else
        {
            // This check is rather superfluous as the one above for digits
            // should handle it.
            throw std::runtime_error(
                "Filename of HGT file in wrong format the "
                "cardial should be followed by two digits.");
        }
    }

    throw std::runtime_error(
        "Filename of HGT file in wrong format the "
        "cardial should be followed by three digits.");
}

HGT::HgtFormat HGT::IdentifyHgtFile(const char* Path)
{
    auto size = std::filesystem::file_size(std::filesystem::path(Path)) / 2;

    if (size == 3601 * 3601) return HgtFormat::SRTM1;
    if (size == 1201 * 1201) return HgtFormat::SRTM3;

    return HgtFormat::Unknown;
}

std::pair<float, float> HGT::LocationFromHgtName(const char* Path)
{
    const auto filename = std::filesystem::path(Path).filename().string();
    std::cout << filename << std::endl;

    if (filename.size () < 7)
    {
        // Expects at a minimum: [NS]##[EW]###
        // Ideally ends with the extention HGT as well.
        throw std::runtime_error("Filename of HGT file in wrong format.");
    }

    const bool isNorthing = filename.front() == 'N' || filename.front() == 'n';
    const bool isSouthing = filename.front() == 'S' || filename.front() == 's';

    if (!isNorthing && !isSouthing)
    {
        throw std::runtime_error("Filename of HGT file in wrong format should "
                                 "start with N(orth) or S(outh).");
    }

    if (std::isdigit(filename[1]) && std::isdigit(filename[2]))
    {
        float northing;
        if (auto [next, ec] = std::from_chars(
                filename.data() + 1, filename.data() + 3, northing);
            ec == std::errc())
        {
            auto longitude = local::ParseLongitude(next);
            return {isNorthing ? northing : -northing, longitude};
        }
        else
        {
            // This check is rather superfluous as the one above for digits
            // should handle it.
            throw std::runtime_error(
                "Filename of HGT file in wrong format the "
                "cardial should be followed by two digits.");
        }
    }

    throw std::runtime_error("Filename of HGT file in wrong format the "
                             "cardial should be followed by two digits.");
}

void HGT::ForEachHeight(const char* Path, HeightCallback Function)
{
    if constexpr (local::UseSingleReadCall)
    {
        // This allocates all the memory up front. It must be done on the
        // heap as 25MB is typically too big for the stack.
        const constexpr auto bufferSize = 3601 * 3601 * sizeof(std::int16_t);
#ifdef NO_STD_BYTE
        std::ifstream input(Path, std::ios::binary | std::ios::ate);
        auto heights =  std::make_unique<char[]>(bufferSize);
#else
        std::basic_ifstream<std::byte> input(
            Path, std::ios::binary | std::ios::ate);
        auto heights = std::make_unique<std::byte[]>(bufferSize);
#endif
        const auto size = input.tellg();
        if (size > bufferSize)
        {
            // We could be strict here and ensure it is the right multiple
            // of 3601 or 1201.
            throw std::runtime_error("File is the wrong size.");
        }

        input.seekg(0);
        input.read(heights.get(), size);

        for (std::size_t i = 0; i < size; i += 2)
        {
            Function(static_cast<std::int16_t>(
                        (heights[i] << 8) | heights[i + 1]));
        }
    }
    else
    {
#ifdef NO_STD_BYTE
        std::ifstream input(Path, std::ios::binary);
        char height[sizeof(std::int16_t)];
#else
        std::basic_ifstream<std::byte> input(Path, std::ios::binary);
        std::byte height[sizeof(std::int16_t)];
#endif

        if (!input.is_open())
        {
            throw std::runtime_error("Failed to open file");
        }

        while (!input.eof())
        {
            if (input.read(height, sizeof(std::uint16_t)))
            {
                Function(static_cast<std::int16_t>((height[0] << 8) | height[1]));
            }
        }
    }
}

void HGT::ForEachHeightWithIndex(
    const char* Path,
    IndexAndHeightCallback Function)
{
    // This tells is the number of rows and columns in the file.
    const auto size = static_cast<int>(IdentifyHgtFile(Path));

    if constexpr (local::UseLambdaForIndex)
    {
        HGT::ForEachHeight(
            Path,
            [x = 0, y = 0, size, Function](std::int16_t Height) mutable
            {
                Function(x, y, Height);

                ++x;
                if (x == size)
                {
                    ++y;
                    x = 0;
                }
            });
    }
    else
    {
        std::basic_ifstream<std::byte> input(Path, std::ios::binary);
        std::byte height[sizeof(std::int16_t)];
        if (!input.is_open())
        {
            throw std::runtime_error("Failed to open file");
        }

        int x = 0;
        int y = 0;
        while (!input.eof())
        {
            if (input.read(height, sizeof(std::uint16_t)))
            {
                Function(
                    x,
                    y,
                    static_cast<std::int16_t>((height[0] << 8) | height[1]));

                ++x;
                if (x == size)
                {
                    ++y;
                    x = 0;
                }
            }
        }
    }
}

#ifdef WITH_HGT_MAIN

int main(int argc, char* argv[])
{
    try
    {
            //"N52W008.hgt",
        const char* filename = (argc > 1) ? argv[1] : "N03W074.hgt";
        const auto [latitude, longitude] =
            HGT::LocationFromHgtName(filename);
        std::cout << latitude << ", " << longitude << std::endl;

        HGT::ForEachHeight(
            filename,
            [](auto Height)
            {
                std::cout << Height << "\n";
            });
    }
    catch (const std::runtime_error& Error)
    {
        std::cerr << Error.what() << std::endl;
        return 1;
    }
    return 0;
}

#endif

//===--------------------------- End of the file --------------------------===//
