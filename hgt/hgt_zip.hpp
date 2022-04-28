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
#include <memory>
#include <string>
#include <utility>

namespace HGT
{
    namespace ZIP
    {
        HGT::HgtFormat IdentifyHgtFile(const char* Path);

        // For each height in the path calls Function(height).
        // The height provided to the callback function is in metres
        void ForEachHeight(const char* Path, HeightCallback Function);

        class Archive;

        // Closes the open ZIP archive.
        void Close(Archive* Zip);

        // Provides a scoped bound resource which will close the archive when
        // an object of this type goes out-of-scope.
        using ArchivePtr = std::unique_ptr<Archive, decltype(&Close)>;

        // Opens the ZIP archive at the given path.
        //
        // If there is an error it throws a std::runtime_error with the
        // details
        ArchivePtr Open(const char* Path);


        // Returns the format of the HGT file within the ZIP archive.
        HGT::HgtFormat IdentifyHgtFile(Archive* Zip);

        // Returns the name of the HGT file within the ZIP archive.
        std::string FileName(Archive* Zip);

        // For each height in the file in the Zip calls Function(height).
        // The height provided to the callback function is in metres
        void ForEachHeight(Archive* Zip, HeightCallback Function);
    }
}

//===--------------------------- End of the file --------------------------===//
#endif
