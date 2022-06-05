#ifndef ASC_ASC_HPP
#define ASC_ASC_HPP
//===---------------------------------------------------------------------===//
//
// NAME         : ASC
// NAMESPACE    : ASC
// PURPOSE      : Provides functions for working with ASCII grid files (.asc).
// COPYRIGHT    : (c) 2022 Sean Donnellan. All Rights Reserved.
// LICENSE      : The MIT License (see LICENSE.txt for details)
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides functions for working with ASC files.
//
//===---------------------------------------------------------------------===//

#include <functional>

namespace ASC
{
    struct Header
    {
        int column_count;
        int row_count;
        double cell_size;
        int lower_left_corner_x;
        int lower_left_corner_y;
        int no_data_value; // Represents the cell has no data in it.
    };

    // Read the header information from the start of the file.
    //
    // This expects the six fields in the header. If an unrecognised field is
    // encounter the program will abort.
    Header ReadFromFile(const char* Path);

    using HeightCallback = std::function<void(double)>;

    // For each height in the path calls Function(height).
    void ReadHeights(const char* Path, HeightCallback Function);
}

//===-------------------------- End of the file --------------------------===//
#endif
