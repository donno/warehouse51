//===----------------------------------------------------------------------===//
//
// NAME         : TIFFTools
// NAMESPACE    : TiffTools
// PURPOSE      : Provides tools for working with TIFF files with elevation.
// COPYRIGHT    : (c) 2020 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
//
//===----------------------------------------------------------------------===/

#include "TiffTools.hpp"

#include "tiffio.h"

#include <charconv>
#include <cstring>
#include <filesystem>
#include <memory>
#include <optional>

namespace
{
  namespace local
  {
    using namespace TiffTools;

    // This tag is used the GDAL library to flag values that contains an ASCII
    // encoded nodata or background pixel value.
    // If this tag is absent there is assume to be no nodata value in effect
    // for the image.
    // If the image has more than one sample it is assumed that all samples
    // have the same nodata value.
    // https://www.awaresystems.be/imaging/tiff/tifftags/gdal_nodata.html
    //
    // Research:
    //  Tag 42113: -32767 [jotunheimen.tif]
    //  Tag 42113: -32768 [LRO_LOLA_DEM_NPolar875_10m.tif]
    constexpr ttag_t GDAL_NODATA { 42113 }; // 0xA481

    // ModelPixelScaleTag = (ScaleX, ScaleY, ScaleZ)
    constexpr ttag_t GEOTIFF_MODELPIXELSCALETAG { 33550 };

    constexpr ttag_t GEOTIFF_MODELTIEPOINTTAG { 33922 };

    // THis is used to keep track of the last registered tag extenter.
    TIFFExtendProc ParentExtender = nullptr;

    template<typename TYPE>
    std::optional<TYPE> NoDataValue(TIFF* Tiff);

    // Defines an axis-aligned rectangle.
    struct Rect
    {
        uint32_t x;
        uint32_t y;
        uint32_t width;
        uint32_t height;
    };

    struct TiledMetadata
    {
        uint32_t imageWidth;
        uint32_t imageLength;
        uint32_t tileWidth;
        uint32_t tileLength;
        uint16_t sampleFormat;
        uint16_t bitsPerSample;

        Vector2D cellSize;

        // Return true if the file is the given format and given size.
        bool Is(uint16_t SampleFormat, uint16_t BitsPerSample) const;

        // Handle the optional no-data fields.
        std::optional<float> noDataValueFloat;
        std::optional<double> noDataValueDouble;
        std::optional<int16_t> noDataValueInt;
        std::optional<uint16_t> noDataValueUnsignedInt;
    };

    // Returns the number of cells that had data.
    template<typename VALUE_TYPE>
    std::size_t WriteTileToGrid(
        Rect Tile,
        const VALUE_TYPE* Values,
        std::optional<VALUE_TYPE> NoDataValue,
        TiffTools::IElevationImporter* Grid);

    template<typename VALUE_TYPE>
    void SaveScanLine(
        uint32_t Row, uint32_t Width,
        const VALUE_TYPE* Values,
        std::optional<VALUE_TYPE> NoDataValue,
        IElevationImporter* Grid);

    template<typename VALUE_TYPE>
    void ReadViaScanLinesInternal(
        TIFF* Tiff,
        std::optional<VALUE_TYPE> NoDataValue,
        IElevationImporter* Importer);

    // Read the information needed from a TIFF for processing a tiled TIFF.
    // This reports warnings and errors to standard error.
    TiledMetadata ReadTiledMetadata(TIFF* Tiff);

    void ReadTile(
        TIFF* Tiff,
        const TiledMetadata& MetaData,
        TiffTools::Point2D LowerLeft,
        tdata_t Buffer,
        uint32_t X, uint32_t Y,
        IElevationImporter* Importer);
  }
}

template<typename TYPE>
std::optional<TYPE> local::NoDataValue(TIFF* Tiff)
{
if defined(__GLIBCXX__) && (__GLIBCXX__ == 20190406 || \
                            __GLIBCXX__ == 20210601)
    // This version of libstd++ doesn't have a std::from_chars() that works
    // with floating-point.
    constexpr bool hasFromChars = !std::is_floating_point_v<TYPE>;
#else
    // Assume we have std::from_chars() which accepts a float for other
    // standard libraries and versions.
    constexpr bool hasFromChars = true;
#endif

    // This tag is ASCII string if it is set.
    const char* stringValue;
    if (TIFFGetField(Tiff, GDAL_NODATA, &stringValue) == 1)
    {
        // The tag exists now parse it.
        TYPE value;
        if constexpr (hasFromChars)
        {
            if (auto [source, errorCode] = std::from_chars(
                    stringValue, stringValue + std::strlen(stringValue), value);
                errorCode == std::errc())
            {
                return std::make_optional(value);
            }
            else
            {
                fprintf(stderr,
                        "Warning: Unable to read string as no data value: "
                        "%s\n",
                        source);
            }
        }
        else if constexpr (std::is_floating_point_v<TYPE>)
        {
            char* end = nullptr;
            if constexpr (std::is_same_v<TYPE, float>)
            {
                value = std::strtof(stringValue, &end);
            }
            else
            {
                static_assert(std::is_same_v<TYPE, double>);
                value = std::strtod(stringValue, &end);
            }

            if (stringValue != end )
            {
                return std::make_optional(value);
            }

            fprintf(stderr,
                    "Warning: Unable to read string as no data value: %s\n",
                    stringValue);
        }
    }

    return {};
}

bool local::TiledMetadata::Is(
    uint16_t SampleFormat,
    uint16_t BitsPerSample) const
{
    return sampleFormat == SampleFormat && bitsPerSample == BitsPerSample;
}

template<typename VALUE_TYPE>
std::size_t local::WriteTileToGrid(
    Rect Tile,
    const VALUE_TYPE* Values,
    std::optional<VALUE_TYPE> NoDataValue,
    IElevationImporter* Grid)
{
    // row and column are within the buffer (values) and x and y are in the
    // grid.
    uint32_t withDataCount = 0;
    for (uint32_t row = 0; row < Tile.height; ++row)
    {
        for (uint32_t column = 0; column < Tile.width; ++column, ++Values)
        {
            if (!NoDataValue || *Values != *NoDataValue)
            {
                Grid->SetValue(Tile.x + column, Tile.height - (Tile.y + row) - 1, *Values);
                ++withDataCount;
            }
            else
            {
                Grid->FlagNoData(Tile.x + column, Tile.height - (Tile.y + row) - 1);
            }
        }
    }

    return withDataCount;
}

template<typename VALUE_TYPE>
void local::SaveScanLine(
    uint32_t Row, uint32_t Width,
    const VALUE_TYPE* Values,
    std::optional<VALUE_TYPE> NoDataValue,
    IElevationImporter* Grid)
{
    auto value = Values;
    for (uint32_t column = 0; column < Width; ++column, ++value)
    {
        if (!NoDataValue || *value != *NoDataValue)
        {
            Grid->SetValue(column, Row, *value);
        }
        else
        {
            Grid->FlagNoData(column, Row);
        }
    }
}

template<typename VALUE_TYPE>
void local::ReadViaScanLinesInternal(
    TIFF* Tiff,
    std::optional<VALUE_TYPE> NoDataValue,
    IElevationImporter* Importer)
{
    uint32_t width, height;
    TIFFGetField(Tiff, TIFFTAG_IMAGEWIDTH, &width);
    TIFFGetField(Tiff, TIFFTAG_IMAGELENGTH, &height);

    uint16_t sampleCount;
    TIFFGetField(Tiff, TIFFTAG_SAMPLESPERPIXEL, &sampleCount);

    if (sampleCount != 1)
    {
        fprintf(stderr, "Warning: Sample count was not 1 but %d. This may not "
                        "work as expected.\n", sampleCount);
    }

    tdata_t buffer = _TIFFmalloc(TIFFScanlineSize(Tiff));

    auto progress = Importer->Progress();
    if (progress) progress->Start(height);

    for (uint32_t row = 0; row < height; ++row)
    {
        // While the documentation showed this approach, it doesn't doesn't seem to be right.
        // Either, the scan line size and read functions knows to do [sample 1, sample 2, sample 3, sample 1, sample]
        // Or each sample is expected to be processed separately, i.e its a different attribute.
        // Imagine if the TIF contained airborne LIDAR, then maybe the samples are used to
        // encode different properties, i.e there are multiple samples (measurements) for each point.
        for (uint16_t s = 0; s < sampleCount; s++)
        {
            TIFFReadScanline(Tiff, buffer, row, s);
        }

        const auto rowFromBottom = height - row - 1;

        const auto values = static_cast<VALUE_TYPE*>(buffer);
        SaveScanLine(rowFromBottom, width, values, NoDataValue, Importer);
        if (progress) progress->StripProcessed();
    }

    if (progress) progress->End();

    _TIFFfree(buffer);
}

local::TiledMetadata local::ReadTiledMetadata(TIFF* Tiff)
{
    TiledMetadata metadata;
    TIFFGetField(Tiff, TIFFTAG_IMAGEWIDTH, &metadata.imageWidth);
    TIFFGetField(Tiff, TIFFTAG_IMAGELENGTH, &metadata.imageLength);
    TIFFGetField(Tiff, TIFFTAG_TILEWIDTH, &metadata.tileWidth);
    TIFFGetField(Tiff, TIFFTAG_TILELENGTH, &metadata.tileLength);
    TIFFGetField(Tiff, TIFFTAG_BITSPERSAMPLE, &metadata.bitsPerSample);
    TIFFGetField(Tiff, TIFFTAG_SAMPLEFORMAT, &metadata.sampleFormat);
    if (TIFFGetField(Tiff, TIFFTAG_SAMPLEFORMAT, &metadata.sampleFormat) != 1)
    {
        // Sample format was not defined, using the default of 1 (unsigned
        // integer data).
        // https://awaresystems.be/imaging/tiff/tifftags/sampleformat.html
        metadata.sampleFormat = SAMPLEFORMAT_UINT;
    }

    metadata.cellSize = TiffTools::CellSize(Tiff);

    const auto bitsPerSample = metadata.bitsPerSample;

    std::optional<float> noDataValueFloat;
    std::optional<double> noDataValueDouble;
    std::optional<int16_t> noDataValueInt;
    std::optional<uint16_t> noDataValueUnsignedInt;
    if (metadata.sampleFormat == SAMPLEFORMAT_IEEEFP)
    {
        printf("Samples are in IEEE floating point format with %d bits per "
               "sample.\n", bitsPerSample);
        if (bitsPerSample == 32)
        {
            noDataValueFloat = local::NoDataValue<float>(Tiff);
        }
        else if (bitsPerSample == 64)
        {
            noDataValueDouble = local::NoDataValue<double>(Tiff);
        }
        else
        {
            fprintf(stderr,
                    "Expected 32-bits/64-bit per sample (32-bit/64-bit IEEE "
                    "float) got %d bits per sample.\n", bitsPerSample);
        }
    }
    else if (metadata.sampleFormat == SAMPLEFORMAT_INT)
    {
        printf("Samples are signed integer.\n");
        if (bitsPerSample == 16)
        {
            noDataValueInt = local::NoDataValue<int16_t>(Tiff);
        }
        else
        {
            fprintf(stderr,
                    "Expected 16-bits per sample (16-bit signed integer) got "
                    "%d bits per sample.\n", bitsPerSample);
        }
    }
    else if (metadata.sampleFormat == SAMPLEFORMAT_UINT)
    {
        printf("Samples are signed integer.\n");
        if (bitsPerSample == 16)
        {
            noDataValueInt = local::NoDataValue<uint16_t>(Tiff);
        }
        else
        {
            fprintf(stderr,
                    "Expected 16-bits per sample (16-bit signed integer) got "
                    "%d bits per sample.\n", bitsPerSample);
        }
    }

    return metadata;
}

void local::ReadTile(
    TIFF* Tiff,
    const TiledMetadata& Metadata,
    TiffTools::Point2D LowerLeft,
    tdata_t Buffer,
    uint32_t X, uint32_t Y,
    IElevationImporter* Importer)
{
    const auto& cellSize = Metadata.cellSize;

    TIFFReadTile(Tiff, Buffer, X, Metadata.imageLength - Y - 1, 0, tsample_t{0});

    // Create a grid just for this tile and then write the data into it.
    Importer->BeginTile(
        Point2D{ LowerLeft.x + X * cellSize.x,
                 LowerLeft.y + Y * cellSize.y },
        Point2D{ LowerLeft.x + (X + Metadata.tileWidth -1) * cellSize.x,
                 LowerLeft.y + (Y + Metadata.tileLength - 1) * cellSize.y },
        cellSize);

    const auto trueTileDimension =
        [](uint32_t Start, uint32_t End, uint32_t Stride)
        {
            if (Start + Stride > End)
            {
                return End - Start;
            }

            return Stride;
        };

    const local::Rect tileExtent =
        { 0, 0, Metadata.tileLength, Metadata.tileWidth };

    // Determine the max width and height to read to. If the image is
    // not an exact multiple of the tile size then remaining tile will
    // be smaller however it be zero-filled outside of the tile area.
    const auto validWidth = trueTileDimension(
        X, Metadata.imageWidth, Metadata.tileWidth);
    const auto validLength = trueTileDimension(
        Y, Metadata.imageLength, Metadata.tileLength);

    std::size_t cellsWithData = 0;
    if (Metadata.Is(SAMPLEFORMAT_INT, 16))
    {
        // This is valid when the sample format is SAMPLEFORMAT_INT and
        // 16-bit.
        auto values = static_cast<int16_t*>(Buffer);
        cellsWithData = WriteTileToGrid(
            tileExtent, values, Metadata.noDataValueInt, Importer);
    }
    else if (Metadata.Is(SAMPLEFORMAT_UINT, 16))
    {
        // This is valid when the sample format is SAMPLEFORMAT_UINT
        // and 16-bit.
        auto values = static_cast<uint16_t*>(Buffer);
        cellsWithData = WriteTileToGrid(
            tileExtent, values, Metadata.noDataValueUnsignedInt,
            Importer);
    }
    else if (Metadata.Is(SAMPLEFORMAT_IEEEFP, 32))
    {
        // This is valid when sample format is SAMPLEFORMAT_IEEEFP and
        // 32-bits.
        auto values = static_cast<float*>(Buffer);
        cellsWithData = WriteTileToGrid(
            tileExtent, values, Metadata.noDataValueFloat, Importer);
    }
    else if (Metadata.Is(SAMPLEFORMAT_IEEEFP, 64))
    {
        // This is valid when sample format is SAMPLEFORMAT_IEEEFP and
        // 64-bits.
        auto values = static_cast<double*>(Buffer);
        cellsWithData = WriteTileToGrid(
            tileExtent, values, Metadata.noDataValueDouble, Importer);
    }
    else
    {
        fprintf(stderr,
                "Unable to read/write this type of data (%d bits).\n",
                Metadata.bitsPerSample);
    }
    Importer->EndTile(X / Metadata.tileWidth,
                      Y / Metadata.tileLength,
                      cellsWithData == 0);
}

void TiffTools::RegisterAdditionalTiffTags()
{
    using namespace local;

    // This lambda must remain C comptabile so it can passed to
    // TIFFSetTagExtender(), so it can't take any captures.
    auto tagExtender = [](TIFF* tif)
    {
        // ModelPixelScaleTag is also known as GeoPixelScale.

        static const TIFFFieldInfo xtiffFieldInfo[] = {
            // GeoTIFF Tags
            { GEOTIFF_MODELPIXELSCALETAG, TIFF_VARIABLE, TIFF_VARIABLE,
              TIFF_DOUBLE, FIELD_CUSTOM,
              true, true, (char*)"ModelPixelScaleTag"},
            { GEOTIFF_MODELTIEPOINTTAG, TIFF_VARIABLE, TIFF_VARIABLE,
                TIFF_DOUBLE, FIELD_CUSTOM,
               true, true, (char*)"ModelTiepointTag" },

            // GDAL Tags
            { GDAL_NODATA, -1,-1, TIFF_ASCII, FIELD_CUSTOM,
              true, false, (char*)"GDALNoDataValue" },
        };

        if (ParentExtender) (*ParentExtender)(tif);

        TIFFMergeFieldInfo(tif, xtiffFieldInfo,
            sizeof(xtiffFieldInfo) / sizeof(xtiffFieldInfo[0]));
    };

    ParentExtender = TIFFSetTagExtender(tagExtender);
}

TiffTools::Vector2D TiffTools::CellSize(TIFF* Tiff)
{
    int16_t count;
    double* scaleXYZ;
    if (TIFFGetField(Tiff, local::GEOTIFF_MODELPIXELSCALETAG, &count,
                     &scaleXYZ) == 1)
    {
        // The Z scale is almost always Z.
        if (count >= 3 && scaleXYZ[2] != 0.0)
        {
            fprintf(stderr,
                    "Warning: Encountered a non-zero Z scale value: %f\n",
                    scaleXYZ[2]);
        }

        return Vector2D{ scaleXYZ[0], scaleXYZ[1] };
    }

    fprintf(stderr,
            "Warning: No Pixel scale tag was present. Don't know what 1-pixel "
            "to N-metres is.\n");

    return Vector2D{1.0, 1.0};
}

std::pair<TiffTools::Point2D, TiffTools::Point2D>
TiffTools::Bounds(TIFF* Tiff, Vector2D CellSize)
{
    // http://docs.opengeospatial.org/DRAFTS/geotiff.pdf

    // Technically, this is going to be tie point count * 6, i.e its actually
    // the number of values that form tie points. There are six values for
    // each tie point.
    int16_t tiePointCount;
    double* tiePoints;
    if (TIFFGetField(Tiff, local::GEOTIFF_MODELTIEPOINTTAG, &tiePointCount,
                     &tiePoints) != 1)
    {
        printf("Unable to determine the model tiepoints..\n");
        return {};
    }

    // Assert that tiePointCount is divisible by 6.

    uint32_t width, height;
    TIFFGetField(Tiff, TIFFTAG_IMAGEWIDTH, &width);
    TIFFGetField(Tiff, TIFFTAG_IMAGELENGTH, &height);

    Point2D lowerLeft { tiePoints[3], tiePoints[4] - height * CellSize.y };
    Point2D upperRight { tiePoints[3] + width * CellSize.x,  tiePoints[4] };

    // The handling of this may be specific to the systems used by
    // IElevationImporter. This part of the importer doesn't support if the
    // raster pixel defines a point rather than an area (the default).
    //
    // This account for the difference in the points and cells and corner vs
    // centres. Ideally, this would be checking for 6.3.1.2 Raster Type Codes
    // from the GeoTIFF specification.
    lowerLeft.x += CellSize.x / 2;
    lowerLeft.y += CellSize.y / 2;
    upperRight.x -= CellSize.x / 2;
    upperRight.y -= CellSize.y / 2;

    return { lowerLeft, upperRight };
}

void TiffTools::ReadViaTiles(TIFF* Tiff, IElevationImporter* Importer)
{
    uint16_t sampleCount;
    TIFFGetField(Tiff, TIFFTAG_SAMPLESPERPIXEL, &sampleCount);

    if (sampleCount != 1)
    {
        fprintf(stderr,
                "Warning: Sample count was not 1 but %d. This may not work as "
                "expected.\n", sampleCount);
    }

    const local::TiledMetadata metadata = local::ReadTiledMetadata(Tiff);
    const auto&& [lowerLeft, upperRight] = Bounds(Tiff, metadata.cellSize);

    tdata_t buffer = _TIFFmalloc(TIFFTileSize(Tiff));

    int16_t orientation = 1;
    TIFFGetField(Tiff, TIFFTAG_ORIENTATION, &orientation);
    if (orientation != 1)
    {
        fprintf(stderr, "Warning: The orientation (%d) is unsupported.\n",
                orientation);
    }

    auto progress = Importer->Progress();
    if (progress) progress->Start(TIFFNumberOfTiles(Tiff));

    for (uint32_t y = 0; y < metadata.imageLength; y += metadata.tileLength)
    {
        for (uint32_t x = 0; x < metadata.imageWidth; x += metadata.tileWidth)
        {
            local::ReadTile(Tiff, metadata, lowerLeft, buffer, x, y, Importer);
            if (progress) progress->TileProcessed();
        }
    }

    if (progress) progress->End();

    _TIFFfree(buffer);
}

void TiffTools::ReadViaScanLines(TIFF* Tiff, IElevationImporter* Importer)
{
    // Treat this as a single tile.
    const auto cellSize = CellSize(Tiff);
    const auto&& [lowerLeft, upperRight] = Bounds(Tiff, cellSize);

    Importer->BeginTile(lowerLeft, upperRight, cellSize);

    uint16_t sampleFormat;
    if (TIFFGetField(Tiff, TIFFTAG_SAMPLEFORMAT, &sampleFormat) != 1)
    {
        // Sample format was not defined, using the default of 1 (unsigned
        // integer data).
        // https://awaresystems.be/imaging/tiff/tifftags/sampleformat.html
        sampleFormat = SAMPLEFORMAT_UINT;
    }

    uint16_t bitsPerSample;
    TIFFGetField(Tiff, TIFFTAG_BITSPERSAMPLE, &bitsPerSample);

    // The default value for this tag is 1 and supporting other values is not
    // a baseline requirement. A value of one means the 0th row represents the
    // visual top of the image, and the 0th column represents the visual
    // left-hand side.
    int16_t orientation = 1;
    TIFFGetField(Tiff, TIFFTAG_ORIENTATION, &orientation);
    if (orientation != 1)
    {
        fprintf(stderr, "Warning: The orientation (%d) is unsupported.\n",
                orientation);
    }

    if (sampleFormat == SAMPLEFORMAT_IEEEFP)
    {
        printf("Samples are in IEEE floating point format.\n");
        if (bitsPerSample == 32)
        {
            auto noDataValue = local::NoDataValue<float>(Tiff);
            local::ReadViaScanLinesInternal(Tiff, noDataValue, Importer);
        }
        else if (bitsPerSample == 64)
        {
            noDataValueDouble = local::NoDataValue<double>(Tiff);
        }
        else
        {
            fprintf(stderr, "Expected 32-bits per sample (32-bit IEEE Float) "
                            "got %d bits per sample.\n", bitsPerSample);
        }
    }
    else if (sampleFormat == SAMPLEFORMAT_INT)
    {
        printf("Samples are signed integer.\n");
        if (bitsPerSample == 8)
        {
            auto noDataValue = local::NoDataValue<int8_t>(Tiff);
            local::ReadViaScanLinesInternal(Tiff, noDataValue, Importer);
        }
        else if (bitsPerSample == 16)
        {
            auto noDataValue = local::NoDataValue<int16_t>(Tiff);
            local::ReadViaScanLinesInternal(Tiff, noDataValue, Importer);
        }
        else
        {
            fprintf(stderr,
                    "Expected 8-bits or 16-bits per sample (8-bit/16-bit "
                    "signed integer) got %d bits per sample.\n",
                    bitsPerSample);
        }
    }
    else if (sampleFormat == SAMPLEFORMAT_UINT)
    {
        printf("Samples are unsigned integer.\n");
        if (bitsPerSample == 8)
        {
            auto noDataValue = local::NoDataValue<uint8_t>(Tiff);
            local::ReadViaScanLinesInternal(Tiff, noDataValue, Importer);
        }
        else if (bitsPerSample == 16)
        {
            auto noDataValue = local::NoDataValue<uint16_t>(Tiff);
            local::ReadViaScanLinesInternal(Tiff, noDataValue, Importer);
        }
        else
        {
            fprintf(stderr,
                    "Expected 8-bits or 16-bits per sample (8-bit/16-bit "
                    "unsigned integer) got %d bits per sample.\n",
                    bitsPerSample);
        }
    }

    Importer->EndTile(0, 0, false);
}
