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
#include <filesystem>
#include <memory>
#include <optional>
#include <string>

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

    Vector2D CellSize(TIFF* Tiff);

    // Returns the lower left and upper right bounds of the image in world
    // space.
    std::pair<Point2D, Point2D> Bounds(TIFF* Tiff, Vector2D CellSize);

    // Returns the number of cells that had data.
    template<typename VALUE_TYPE>
    std::size_t WriteTileToGrid(
        uint32 X, uint32 Y, uint32 Width, uint32 Height,
        const VALUE_TYPE* Values,
        std::optional<VALUE_TYPE> NoDataValue,
        TiffTools::IElevationImporter* Grid);

    template<typename VALUE_TYPE>
    void SaveScanLine(
        uint32 Row, uint32 Width,
        const VALUE_TYPE* Values,
        std::optional<VALUE_TYPE> NoDataValue,
        IElevationImporter* Grid);

    template<typename VALUE_TYPE>
    void ReadViaScanLinesInternal(
        TIFF* Tiff,
        std::optional<VALUE_TYPE> NoDataValue,
        IElevationImporter* Importer);
  }
}

template<typename TYPE>
std::optional<TYPE> local::NoDataValue(TIFF* Tiff)
{
    // This tag is ASCII string if it is set.
    const char* stringValue;
    if (TIFFGetField(Tiff, GDAL_NODATA, &stringValue) == 1)
    {
        // The tag exists now parse it.
        TYPE value;
        if (auto [source, errorCode] = std::from_chars(
                stringValue, stringValue + strlen(stringValue), value);
            errorCode == std::errc())
        {
            return std::make_optional(value);
        }
        else
        {
            fprintf(stderr,
                    "Warning: Unable to read string as no data value: %s\n",
                    source);
        }
    }

    return {};
}

TiffTools::Vector2D local::CellSize(TIFF* Tiff)
{
    int16 count;
    double* scaleXYZ;
    if (TIFFGetField(Tiff, GEOTIFF_MODELPIXELSCALETAG, &count, &scaleXYZ) == 1)
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
local::Bounds(TIFF* Tiff, Vector2D CellSize)
{
    // http://docs.opengeospatial.org/DRAFTS/geotiff.pdf

    // Technically, this is going to be tie point count * 6, i.e its actually
    // the number of values that form tie points. There are six values for
    // each tie point.
    int16 tiePointCount;
    double* tiePoints;
    if (TIFFGetField(Tiff, GEOTIFF_MODELTIEPOINTTAG, &tiePointCount,
                     &tiePoints) != 1)
    {
        printf("Unable to determine the model tiepoints..\n");
        return {};
    }

    // Assert that tiePointCount is divisible by 6.

    uint32 width, height;
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

template<typename VALUE_TYPE>
std::size_t local::WriteTileToGrid(
    uint32 X, uint32 Y, uint32 Width, uint32 Height,
    const VALUE_TYPE* Values,
    std::optional<VALUE_TYPE> NoDataValue,
    IElevationImporter* Grid)
{
    // row and column are within the buffer (values) and x and y are in the
    // grid.
    uint32 withDataCount = 0;
    for (uint32 row = 0; row < Height; ++row)
    {
        for (uint32 column = 0; column < Width; ++column, ++Values)
        {
            if (!NoDataValue || *Values != *NoDataValue)
            {
                Grid->SetValue(X + column, Height - (Y + row) - 1, *Values);
                ++withDataCount;
            }
            else
            {
                Grid->FlagNoData(X + column, Height - (Y + row) - 1);
            }
        }
    }

    return withDataCount;
}

template<typename VALUE_TYPE>
void local::SaveScanLine(
    uint32 Row, uint32 Width,
    const VALUE_TYPE* Values,
    std::optional<VALUE_TYPE> NoDataValue,
    IElevationImporter* Grid)
{
    auto value = Values;
    for (uint32 column = 0; column < Width; ++column, ++value)
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
    uint32 width, height;
    TIFFGetField(Tiff, TIFFTAG_IMAGEWIDTH, &width);
    TIFFGetField(Tiff, TIFFTAG_IMAGELENGTH, &height);

    uint16 sampleCount;
    TIFFGetField(Tiff, TIFFTAG_SAMPLESPERPIXEL, &sampleCount);

    if (sampleCount != 1)
    {
        fprintf(stderr, "Warning: Sample count was not 1 but %d. This may not "
                        "work as expected.\n", sampleCount);
    }

    tdata_t buffer = _TIFFmalloc(TIFFScanlineSize(Tiff));

    auto progress = Importer->Progress();
    if (progress) progress->Start(height);

    for (uint32 row = 0; row < height; ++row)
    {
        // While the documentation showed this approach, it doesn't doesn't seem to be right.
        // Either, the scan line size and read functions knows to do [sample 1, sample 2, sample 3, sample 1, sample]
        // Or each sample is expected to be processed separately, i.e its a different attribute.
        // Imagine if the TIF contained airborne LIDAR, then maybe the samples are used to
        // encode different properties, i.e there are multiple samples (measurements) for each point.
        for (uint16 s = 0; s < sampleCount; s++)
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

void TiffTools::ReadViaTiles(TIFF* Tiff, IElevationImporter* Importer)
{
    uint16 sampleCount;
    TIFFGetField(Tiff, TIFFTAG_SAMPLESPERPIXEL, &sampleCount);

    if (sampleCount != 1)
    {
        fprintf(stderr,
                "Warning: Sample count was not 1 but %d. This may not work as "
                "expected.\n", sampleCount);
    }

    uint16 bitsPerSample;
    TIFFGetField(Tiff, TIFFTAG_BITSPERSAMPLE, &bitsPerSample);

    uint32 imageWidth, imageLength;
    uint32 tileWidth, tileLength;
    TIFFGetField(Tiff, TIFFTAG_IMAGEWIDTH, &imageWidth);
    TIFFGetField(Tiff, TIFFTAG_IMAGELENGTH, &imageLength);
    TIFFGetField(Tiff, TIFFTAG_TILEWIDTH, &tileWidth);
    TIFFGetField(Tiff, TIFFTAG_TILELENGTH, &tileLength);

    uint16 sampleFormat;
    TIFFGetField(Tiff, TIFFTAG_SAMPLEFORMAT, &sampleFormat);
    std::optional<float> noDataValueFloat;
    std::optional<double> noDataValueDouble;
    std::optional<int16> noDataValueInt;
    std::optional<uint16> noDataValueUnsignedInt;
    if (sampleFormat == SAMPLEFORMAT_IEEEFP)
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
    else if (sampleFormat == SAMPLEFORMAT_INT)
    {
        printf("Samples are signed integer.\n");
        if (bitsPerSample == 16)
        {
            noDataValueInt = local::NoDataValue<int16>(Tiff);
        }
        else
        {
            fprintf(stderr,
                    "Expected 16-bits per sample (16-bit signed integer) got "
                    "%d bits per sample.\n", bitsPerSample);
        }
    }
    else if (sampleFormat == SAMPLEFORMAT_UINT)
    {
        printf("Samples are signed integer.\n");
        if (bitsPerSample == 16)
        {
            noDataValueInt = local::NoDataValue<uint16>(Tiff);
        }
        else
        {
            fprintf(stderr,
                    "Expected 16-bits per sample (16-bit signed integer) got "
                    "%d bits per sample.\n", bitsPerSample);
        }
    }

    const auto cellSize = local::CellSize(Tiff);
    const auto&& [lowerLeft, upperRight] = local::Bounds(Tiff, cellSize);

    tdata_t buffer = _TIFFmalloc(TIFFTileSize(Tiff));

    int16 orientation = 1;
    TIFFGetField(Tiff, TIFFTAG_ORIENTATION, &orientation);
    if (orientation != 1)
    {
        fprintf(stderr, "Warning: The orientation (%d) is unsupported.\n",
                orientation);
    }

    // TODO: orientation isn't being used here.

    using local::WriteTileToGrid;

    auto progress = Importer->Progress();
    if (progress) progress->Start(TIFFNumberOfTiles(Tiff));

    uint32 tile = 0;
    for (uint32 y = 0; y < imageLength; y += tileLength)
    {
        for (uint32 x = 0; x < imageWidth; x += tileWidth)
        {
            TIFFReadTile(Tiff, buffer, x, imageLength - y - 1, 0, tsample_t{0});
            ++tile;

            // Create a grid just for this tile and then write the data into it.
            Importer->BeginTile(
                Point2D{ lowerLeft.x + x * cellSize.x,
                            lowerLeft.y + y * cellSize.y },
                Point2D{ lowerLeft.x + (x + tileWidth -1) * cellSize.x,
                            lowerLeft.y + (y + tileLength - 1) * cellSize.y },
                cellSize);

            std::size_t cellsWithData = 0;
            if (sampleFormat == SAMPLEFORMAT_INT && bitsPerSample == 16)
            {
                // This is valid when the sample format is SAMPLEFORMAT_INT and
                // 16-bit.
                auto values = static_cast<int16*>(buffer);
                cellsWithData = WriteTileToGrid(
                    0, 0, tileLength, tileWidth, values, noDataValueInt,
                    Importer);
            }
            else if (sampleFormat == SAMPLEFORMAT_UINT && bitsPerSample == 16)
            {
                // This is valid when the sample format is SAMPLEFORMAT_UINT
                // and 16-bit.
                auto values = static_cast<uint16*>(buffer);
                cellsWithData = WriteTileToGrid(
                    0, 0, tileLength, tileWidth, values,
                    noDataValueUnsignedInt, Importer);
            }
            else if (sampleFormat == SAMPLEFORMAT_IEEEFP && bitsPerSample == 32)
            {
                // This is valid when sample format is SAMPLEFORMAT_IEEEFP and
                // 32-bits.
                auto values = static_cast<float*>(buffer);
                cellsWithData = WriteTileToGrid(
                    0, 0, tileLength, tileWidth, values, noDataValueFloat,
                    Importer);
            }
            else if (sampleFormat == SAMPLEFORMAT_IEEEFP && bitsPerSample == 64)
            {
                // This is valid when sample format is SAMPLEFORMAT_IEEEFP and
                // 64-bits.
                auto values = static_cast<double*>(buffer);
                cellsWithData = WriteTileToGrid(
                    0, 0, tileLength, tileWidth, values, noDataValueDouble,
                    Importer);
            }
            else
            {
                fprintf(stderr,
                        "Unable to read/write this type of data (%d bits).\n",
                        bitsPerSample);
            }

            Importer->EndTile(x / tileWidth, y / tileLength,
                              cellsWithData == 0);
            if (progress) progress->TileProcessed();
        }
    }

    if (progress) progress->End();

    _TIFFfree(buffer);
}

void TiffTools::ReadViaScanLines(TIFF* Tiff, IElevationImporter* Importer)
{
    // Treat this as a single tile.
    const auto cellSize = local::CellSize(Tiff);
    const auto&& [lowerLeft, upperRight] = local::Bounds(Tiff, cellSize);

    Importer->BeginTile(lowerLeft, upperRight, cellSize);

    uint16 sampleFormat;
    TIFFGetField(Tiff, TIFFTAG_SAMPLEFORMAT, &sampleFormat);

    uint16 bitsPerSample;
    TIFFGetField(Tiff, TIFFTAG_BITSPERSAMPLE, &bitsPerSample);

    // The default value for this tag is 1 and supporting other values is not
    // a baseline requirement. A value of one means the 0th row represents the
    // visual top of the image, and the 0th column represents the visual
    // left-hand side.
    int16 orientation = 1;
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
            auto noDataValue = local::NoDataValue<int8>(Tiff);
            local::ReadViaScanLinesInternal(Tiff, noDataValue, Importer);
        }
        else if (bitsPerSample == 16)
        {
            auto noDataValue = local::NoDataValue<int16>(Tiff);
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
            auto noDataValue = local::NoDataValue<uint8>(Tiff);
            local::ReadViaScanLinesInternal(Tiff, noDataValue, Importer);
        }
        else if (bitsPerSample == 16)
        {
            auto noDataValue = local::NoDataValue<uint16>(Tiff);
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
