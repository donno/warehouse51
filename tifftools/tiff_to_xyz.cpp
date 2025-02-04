//===----------------------------------------------------------------------===//
//
// NAME         : tiff_to_xyz
// PURPOSE      : Convert a DEM in GeoTIFF format to ASCII Gridded XYZ format.
// COPYRIGHT    : (c) 2025 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
//
//===----------------------------------------------------------------------===/

#include "TiffTools.hpp"

#include <tiffio.h>

#include <memory>

#include <stdio.h>

// Imports the elevation from GeoTIFF and exports to the XYZ format.
struct XyzExporter : public TiffTools::IElevationImporter
{
  XyzExporter(TiffTools::Point2D LowerBound, FILE* Output)
  : myOverallLowerBound(LowerBound), myOutput(Output) {}

  void BeginTile(TiffTools::Point2D LowerBound,
                 TiffTools::Point2D UpperBound,
                 TiffTools::Vector2D CellSize) override;
  void EndTile(int TileIndexX, int TileIndexY, bool DiscardTile) override {}
  void SetValue(int X, int Y, double Value) override;
  void FlagNoData(int X, int Y) override {}

  // Updated by BeginTile().
  int myTileX = 0;
  int myTileY = 0;
  TiffTools::Point2D myTileLowerBound;

  TiffTools::Point2D myOverallLowerBound;
  TiffTools::Vector2D myTileCellSize;

  FILE* myOutput;
};

void XyzExporter::BeginTile(
    TiffTools::Point2D LowerBound,
    TiffTools::Point2D UpperBound,
    TiffTools::Vector2D CellSize)
{
    myTileLowerBound = LowerBound;
    myTileX = static_cast<int>((LowerBound.x - myOverallLowerBound.x) / CellSize.x);
    myTileY = static_cast<int>((LowerBound.y - myOverallLowerBound.y) / CellSize.y);
    myTileCellSize = CellSize;
}

void XyzExporter::SetValue(int X, int Y, double Value)
{
    // X and Y are the index within a tile.
    const auto pixelX = myTileX + X;
    const auto pixelY = myTileY + Y;
    const auto worldZ = Value;

    // While debugging, use this to figure out how the indexing is wrong.
    // This has already helped fix one bug, however it means the Value is
    // wrong for some of the data.
    //printf("%d %d %.f\n", pixelX, pixelY, worldZ);
    const auto worldX = myTileLowerBound.x + X * myTileCellSize.x;
    const auto worldY = myTileLowerBound.y + Y * myTileCellSize.y;
    fprintf(myOutput, "%f %f %f\n", worldX, worldY, worldZ);
}

int main(int argc, char* argv[])
{
    if (argc != 2 && argc != 3)
    {
        fprintf(stderr, "usage: %s tiff_path [xyz_path]\n", argv[0]);
        return 1;
    }

    TiffTools::RegisterAdditionalTiffTags();

    TIFF* tif = TIFFOpen(argv[1], "r");
    if (!tif)
    {
        fprintf(stderr, "Failed to open %s\n", argv[1]);
        return 1;
    }

    std::unique_ptr<TIFF, void (*)(TIFF*)> tiff(tif, TIFFClose);

    FILE* output = argc == 3 ? fopen(argv[2], "w") : stdout;
    try
    {
        const auto&& [lowerLeft, upperRight] = 
            TiffTools::Bounds(tif, TiffTools::CellSize(tif));
        XyzExporter importer(lowerLeft, output);
        if (TIFFIsTiled(tif))
        {
            ReadViaTiles(tif, &importer);
        }
        else
        {
            ReadViaScanLines(tif, &importer);
        }
    }
    catch(const std::exception& exception)
    {
        fprintf(stderr, "%s\n", exception.what());
        return 1;
    }

    if (argc == 3) fclose(output);

    return 0;
}
