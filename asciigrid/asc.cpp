//===----------------------------------------------------------------------===//
//
// NAME         : ASC
// NAMESPACE    : ASC
// PURPOSE      : Provides functions for working with ASCII grid files (.asc).
// COPYRIGHT    : (c) 2022 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides functions for working with ASC files.
//
// The format is as follows:
// - ncols <integer>
// - nrows <integer>
// - xllcorner <integer>
// - yllcorner <integer>
// - cellsize  <integer>
// - NODATA_value <integer>
// - <floating-point> * $ncol * $nrows
//
// The whitespace between the key and value at the start can vary.
//
// xllcorner and yllcorner are the coordinates of the lower left corner of the
// lower left cell.
//
// Instead of corner there can be centre instead, this isn't supported.
//
// Compiling: (MSVC) cl /EHsc /std:c++17 /nologo /DWITH_ASC_MAIN asc.cpp
//                   clang++ -std=c++20 -DWITH_ASC_MAIN asc.cpp
//                   g++-11 -std=c++20 -DWITH_ASC_MAIN asc.cpp
//
//===----------------------------------------------------------------------===//

#include "asc.hpp"

#include <charconv>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>

namespace
{
    namespace local
    {
        // The number of fields at the start of the file that form the header.
        const int field_count = 6;
    }
}

ASC::Header ASC::ReadFromFile(const char* Path)
{
    std::ifstream input(Path);

    ASC::Header header;

    for (int field_index = 0; !input.eof() && field_index < local::field_count;
         ++field_index)
    {
        // TODO: Handle errors cases.
        std::string key;
        input >> key;
        if (key == "ncols")
        {
            input >> header.column_count;
        }
        else if (key == "nrows")
        {
            input >> header.row_count;
        }
        else if (key == "cellsize")
        {
            input >> header.cell_size;
        }
        else if (key == "xllcorner")
        {
            input >> header.lower_left_corner_x;
        }
        else if (key == "yllcorner")
        {
            input >> header.lower_left_corner_y;
        }
        else if (key == "NODATA_value")
        {
            input >> header.no_data_value;
        }
        else
        {
            std::cerr << "unrecognised key: \'" << key << "\'" << std::endl;
            std::abort();
        }
    }

    return header;
}

void ASC::ReadHeights(const char* Path, HeightCallback Function)
{
    constexpr const bool read_line_at_time = true;

    std::ifstream input(Path);

    // Skip the fields.
    for (int i = 0; i < local::field_count; ++i)
    {
        input.ignore(1024, '\n');
    }

    if constexpr (read_line_at_time)
    {
        std::string line;
        while (std::getline(input, line))
        {
            double value;
            const auto end = line.data() + line.size();
            for (const char* next = line.data(); next != end;)
            {
                auto [ptr, ec] { std::from_chars(next, end, value) };

                // TODO: This should not be printing inside of this function.
                if (ec == std::errc())
                {
                    Function(value);
                }
                else if (ec == std::errc::invalid_argument)
                {
                    fprintf(stderr, "Input was not a number, %s.\n", next);
                }
                else if (ec == std::errc::result_out_of_range)
                {
                    fprintf(stderr, "This number was outside the appliable range.\n");
                }

                // The general approach would be find the first non-space character.
                if (ptr && *ptr == ' ') ++ptr;

                next = ptr;
            }
        }
    }
    else
    {
        double value;
        while (!input.eof())
        {
            input >> value;
            if (input.good())
            {
                Function(value);
            }
        }
    }
}

#ifdef WITH_ASC_MAIN
#include <stdio.h>

int main(int argc, const char* argv[])
{
    if (argc == 1)
    {
        fprintf(stderr, "usage: %s <path-to-asc-file>\n", argv[0]);
        return 1;
    }

    ASC::Header header = ASC::ReadFromFile(argv[1]);
    printf("%d by %d at (%d, %d) with size %f\n", header.column_count,
           header.row_count, header.lower_left_corner_x,
           header.lower_left_corner_y, header.cell_size);
    printf("Missing data value: %d\n", header.no_data_value);

    std::size_t count = 0;
    ASC::ReadHeights(argv[1], [&count](double value)
    {
        printf("%.4f\n", value);
        ++count;
    });

    printf("Read: %zu heights.\n", count);

    return 0;
}

#endif

//===--------------------------- End of the file --------------------------===//
