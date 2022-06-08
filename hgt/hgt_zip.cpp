//===----------------------------------------------------------------------===//
//
// NAME         : HGT_ZIP
// SUMMARY      : Provides functions for working with HGT files inside a ZIP.
// COPYRIGHT    : (c) 2022 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : This utilises libzip to work with the ZIP files.
//
// Building with MSVC:
// cl /nologo /EHsc /std:c++20 hgt_zip.cpp /DWITH_HGT_MAIN
//   This also needs the include path for libzip and the path to the zip.lib
//   as well.
// g++-11 -O1 -g -std=c++20 -DWITH_HGT_MAIN hgt_zip.cpp  -lzip
//
// Note: WITH_HGT_MAIN is only needed when compiling an executable that can be
// run for testing purposes.
//
//===----------------------------------------------------------------------===//

#include "hgt_zip.hpp"

#include <zip.h>

#include <cstddef>
#include <limits>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string_view>

namespace
{
    namespace local
    {
        using zip_ptr_t = std::unique_ptr<zip_t, decltype(&zip_close)>;

        // If true then the entire file will be loaded into memory.
        // This is 3601 * 3601 * 2 bytes (~25MB) for a SRTM1 and 1201 * 1201 *
        // 2 bytes (~3MB). Keep in mind the effects of this if doing this in
        // parallel.
        constexpr bool UseSingleReadCall = true;

        // Opens the ZIP file at the given path.
        //
        // Raises std::runtime_error if it is unable to open a ZIP at the given
        // path.
        zip_ptr_t OpenFile(const char* Path);

        // Returns the index of the HGT file in the ZIP. If no result is found
        // returns std::numeric_limits<zip_uint64_t>::max().
        zip_uint64_t FindHgtInZip(zip_t *Zip);
    }
}

class HGT::ZIP::Archive
{
    local::zip_ptr_t myZip;
    zip_uint64_t myHgtIndex;
    zip_stat_t myHgtStat;

public:
    Archive(const char* Path);

    zip_t* Zip() { return myZip.get(); }
    zip_uint64_t HgtIndex() const { return myHgtIndex; }
    const char* HgtName() const { return myHgtStat.name; }

    // Determine the format of the HGT from its uncompressed file size.
    HGT::HgtFormat Format() const;
};


local::zip_ptr_t local::OpenFile(const char* Path)
{
    int error;
#ifdef HGT_ZIP_WITH_MUTEX
    // libzip uses mktime() which is often not thread safe as it does timezone
    // conversions.
    static std::mutex zip_opener;
    zip_opener.lock();
    auto zip = zip_ptr_t{zip_open(Path, ZIP_RDONLY, &error), &zip_close};
    zip_opener.unlock();
#else
    auto zip = zip_ptr_t{zip_open(Path, ZIP_RDONLY, &error), &zip_close};
#endif

    if (zip)
    {
        return zip;
    }

    if (error == ZIP_ER_OPEN)
    {
        throw std::runtime_error(
            "The file specified by path could not be opened.");
    }
    else if (error == ZIP_ER_NOENT)
    {
        throw std::runtime_error(
            "The file specified by path does not exist.");
    }
    else if (error == ZIP_ER_NOZIP)
    {
        throw std::runtime_error(
            "The file specified by path is not a ZIP file.");
    }
    else if (error == ZIP_ER_MEMORY)
    {
        throw std::runtime_error(
            "The file specified by path could not be opened as the required "
            "memory could not be allocated.");
    }
    else if (error = ZIP_ER_READ)
    {
        // This should check errno for details.
        throw std::runtime_error(
            "A read error occurred when reading ZIP file.");
    }

    throw std::runtime_error(
        "An unknown error occurred when opening ZIP file.");
}

zip_uint64_t local::FindHgtInZip(zip_t *Zip)
{
    const auto entryCount = zip_get_num_entries(Zip, ZIP_FL_UNCHANGED);
    for (zip_uint64_t index = 0; index < entryCount; ++index)
    {
        const auto name = zip_get_name(Zip, index, ZIP_FL_ENC_GUESS);
        if (std::string_view(name).ends_with(".hgt"))
        {
            return index;
        }
    }

    return std::numeric_limits<zip_uint64_t>::max();
}

HGT::HgtFormat HGT::ZIP::IdentifyHgtFile(const char* Path)
{
    const Archive archive(Path);
    return archive.Format();
}

void HGT::ZIP::ForEachHeight(const char *Path, HeightCallback Function)
{
    Archive archive(Path);
    return ForEachHeight(&archive, std::move(Function));
}

HGT::ZIP::Archive::Archive(const char* Path)
: myZip(local::OpenFile(Path))
{
    // Find the file with the .hgt suffix.
    myHgtIndex = local::FindHgtInZip(myZip.get());
    if (myHgtIndex == std::numeric_limits<zip_uint64_t>::max())
    {
        throw std::runtime_error(
            "The file specified by path does not contain a HGT file.");
    }

    zip_stat_init(&myHgtStat);
    if (zip_stat_index(myZip.get(), myHgtIndex, ZIP_FL_ENC_GUESS,
        &myHgtStat) != 0)
    {
        throw std::runtime_error(
            "Unable to information about the HGT file within the ZIP.");
    }
}

HGT::HgtFormat HGT::ZIP::Archive::Format() const
{
    const auto size = myHgtStat.size / 2;

    if (size == 3601 * 3601) return HgtFormat::SRTM1;
    if (size == 1201 * 1201) return HgtFormat::SRTM3;

    return HgtFormat::Unknown;
}

void HGT::ZIP::Close(Archive* Zip)
{
    // By providing the delete within this translation unit it allows Archive
    // to essentally be a pointer-to-implementation.
    delete Zip;
}

HGT::ZIP::ArchivePtr HGT::ZIP::Open(const char* Path)
{
    return ArchivePtr{new Archive(Path), &Close};
}

HGT::HgtFormat HGT::ZIP::IdentifyHgtFile(Archive* Zip)
{
    return Zip->Format();
}

std::string HGT::ZIP::FileName(Archive* Zip)
{
    return {Zip->HgtName()};
}

void HGT::ZIP::ForEachHeight(Archive* Zip, HeightCallback Function)
{
    using zip_file_ptr_t = std::unique_ptr<zip_file_t, decltype(&zip_fclose)>;

    zip_file_ptr_t file{zip_fopen_index(Zip->Zip(), Zip->HgtIndex(), 0),
                        &zip_fclose};

    if (!file)
    {
        throw std::runtime_error("Failed to open HGT file within the ZIP.");
    }

    if constexpr (local::UseSingleReadCall)
    {
        // This allocates all the memory up front. It must be done on the
        // heap as 25MB is typically too big for the stack.
        const constexpr auto bufferSize = 3601 * 3601 * sizeof(std::int16_t);
        auto heights = std::make_unique<std::byte[]>(bufferSize);
        const auto readCount =
            zip_fread(file.get(), heights.get(), bufferSize);

        if (readCount != bufferSize)
        {
            throw std::runtime_error("File is wrong size");
        }

        for (std::size_t i = 0; i < readCount; i += 2)
        {
            Function(static_cast<std::int16_t>(
                        (heights[i] << 8) | heights[i + 1]));
        }
    }
    else
    {
        throw std::runtime_error(
            "No runtime support for using multiple read calls.");
    }
}

#ifdef WITH_HGT_MAIN

#include <iostream>

int main()
{
    try
    {
        const auto format =
            HGT::ZIP::IdentifyHgtFile("NASADEM_HGT_n00e013.zip");
        std::cout << "Format : " << static_cast<int>(format) << std::endl;

        HGT::ZIP::ForEachHeight(
            "NASADEM_HGT_n00e013.zip",
            [](auto Height)
            {
                std::cout << Height << "\n";
            });
    }
    catch (const std::runtime_error &Error)
    {
        std::cerr << Error.what() << std::endl;
        return 1;
    }
    return 0;
}

#endif
