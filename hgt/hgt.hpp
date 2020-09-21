#ifndef HGT_HGT_HPP
#define HGT_HGT_HPP
//===----------------------------------------------------------------------===//
//
// NAME         : HGT
// NAMESPACE    : HGT
// PURPOSE      : Provides functions for working with HGT files.
// COPYRIGHT    : (c) 2020 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides functions for working with HGT (height) files which
//                are a data file of the Shuttle Radar Topography Mission
//                (SRTM).
//
// The functions it provide enable:
// - identifying the type of HGT file which is needed for determing the number
//   of rows and columns.
// - read the heights from a HGT file
// - parsing the filenames to determine the latitude and longitude.
//
//===----------------------------------------------------------------------===//

#include <cstdint>
#include <functional>
#include <utility>

namespace HGT
{
    // The height value that represents no data (height) for a given cell.
    const auto NoDataValue = -32768;

    // The format of the HGT file also tells you the row and column counts.
    enum class HgtFormat
    {
        Unknown = 0,
        SRTM1 = 3601, // One arc-second (~30m)
        SRTM3 = 1201, // Three arc-seconds (~90m)
    };

    HgtFormat IdentifyHgtFile(const char* Path);

    // Return the latitude and longitude of the lower-left corner of the file.
    std::pair<float, float> LocationFromHgtName(const char* Path);

    using HeightCallback = std::function<void(std::int16_t)>;
    using IndexAndHeightCallback =
        std::function<void(std::int16_t, std::int16_t, std::int16_t)>;

    // For each height in the path calls Function(height).
    // The height provided to the callback function is in metres
    void ForEachHeight(const char* Path, HeightCallback Function);

    // Provides the index (X and Y) in addition to the height.
    // The height provided to the callback function is in metres
    //
    // The Function will be provided with (xIndex, yIndex, height).
    void ForEachHeightWithIndex(
        const char* Path, IndexAndHeightCallback Function);
}

//===--------------------------- End of the file --------------------------===//
#endif
