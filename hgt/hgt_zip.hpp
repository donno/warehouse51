#ifndef HGT_HGT_ZIP_HPP
#define HGT_HGT_ZIP_HPP
//===----------------------------------------------------------------------===//
//
// NAME         : HGT_ZIP
// NAMESPACE    : HGT
// PURPOSE      : Provides functions for working with HGT files inside a ZIP.
// COPYRIGHT    : (c) 2022 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides functions for working with HGT (height) files which
//                are a data file of the Shuttle Radar Topography Mission
//                (SRTM) that are inside a ZIP.
//
// This depends on libzip by Dieter Baron and Thomas Klausner.
//
//===----------------------------------------------------------------------===//

#include "hgt.hpp"

#include <cstdint>
#include <functional>
#include <utility>

namespace HGT
{
    namespace ZIP
    {
        HGT::HgtFormat IdentifyHgtFile(const char* Path);

        // For each height in the path calls Function(height).
        // The height provided to the callback function is in metres
        void ForEachHeight(const char* Path, HeightCallback Function);

        // TODO: Add a version that can open the ZIP once, and query the
        // format then read the heights.
    }
}

//===--------------------------- End of the file --------------------------===//
#endif
