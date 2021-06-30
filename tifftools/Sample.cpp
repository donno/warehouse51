//===----------------------------------------------------------------------===//
//
// NAME         : Sample
// PURPOSE      : Provides a sample program for TIFFTools.
// COPYRIGHT    : (c) 2020 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
//
// Known issues
// ------------
// The results for tiled data where the image size is not a mutliple of the
// tile will be incorrect.
//
//===----------------------------------------------------------------------===/

#include "TiffTools.hpp"

#include "tiffio.h"

#include <memory>
#include <stdio.h>

// Computes the min, max and average elevation across a TIFF file.
// TODO: provide per tile information to.
struct MinMaxAverageElevation : public TiffTools::IElevationImporter
{
  void BeginTile(TiffTools::Point2D LowerBound,
                 TiffTools::Point2D UpperBound,
                 TiffTools::Vector2D CellSize) override {}
  void EndTile(int TileIndexX, int TileIndexY, bool DiscardTile) override {}
  void SetValue(int X, int Y, double Value) override;
  void FlagNoData(int X, int Y) override {}

  double Average() const { return mySum / myCount; }

  double myMinimum = std::numeric_limits<double>::max();
  double myMaximum = std::numeric_limits<double>::lowest();
  double mySum = 0.0;
  std::size_t myCount = 0;
};

void MinMaxAverageElevation::SetValue(int X, int Y, double Value)
{
  if (Value < myMinimum) myMinimum = Value;
  if (Value > myMaximum) myMaximum = Value;

  mySum += Value;
  ++myCount;
}

int main(int argc, char* argv[])
{
    if (argc != 2)
    {
        printf("usage: %s tiff_path\n", argv[0]);
        return 1;
    }

    TiffTools::RegisterAdditionalTiffTags();

    TIFF* tif = TIFFOpen(argv[1], "r");
    if (!tif)
    {
        printf("Failed to open %s\n", argv[1]);
        return 1;
    }

    std::unique_ptr<TIFF, void (*)(TIFF*)> tiff(tif, TIFFClose);

    try
    {
        MinMaxAverageElevation importer;
        if (TIFFIsTiled(tif))
        {
            printf("Tile count: %d\n", TIFFNumberOfTiles(tif));
            ReadViaTiles(tif, &importer);
        }
        else
        {
            ReadViaScanLines(tif, &importer);
        }

        printf("TIFF file: %s\n", argv[1]);
        printf("Minimum: %f\n", importer.myMinimum);
        printf("Maximum: %f\n", importer.myMaximum);
        printf("Average: %f\n", importer.Average());
    }
    catch(const std::exception& exception)
    {
        fprintf(stderr, "%s\n", exception.what());
    }
}
