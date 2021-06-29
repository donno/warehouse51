#ifndef TIFF_TOOLS_HPP
#define TIFF_TOOLS_HPP
//===----------------------------------------------------------------------===//
//
// NAME         : TIFFTools
// NAMESPACE    : TiffTools
// PURPOSE      : Provides tools for working with TIFF files with elevation.
// COPYRIGHT    : (c) 2020 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides tools for working with TIFF files which represent
//                digital elevation models, that is to say not photographs.
//
// The IElevationImporter interface provides a way to retrieve information
// about the elevation in an abstract way. At this time it converts all height
// values to a double-precision floating point number (64-bit float).
//
// The basic use is as follows:
// - Define a class that implements IElevationImporter
// - Call RegisterAdditionalTiffTags() early in main().
// - Open the TIFF file (see libtiff for details)
// - Check TIFFIsTiled() - this is a libtiff function.
// - Call ReadViaTiles() if true otherwise ReadViaScanLines().
// - Close the TIFF file.
//
//===----------------------------------------------------------------------===/

#include <utility>

#include <tiffio.h>

namespace TiffTools
{
  struct Point2D
  {
      double x;
      double y;
  };

  struct Vector2D
  {
      double x;
      double y;
  };

  class IProgress
  {
  public:
    // This is called at the start when the number of tiles or strips is known.
    virtual void Start(int TileOrStripCount) = 0;

    // This is called when a tile has been processed, such that the progress
    // should be incremented.
    virtual void TileProcessed() = 0;

    // This is called when a strip has been processed, such that the progress
    // should be incremented.
    virtual void StripProcessed() = 0;

    // This is called when all the tiles/strips have been processed.
    virtual void End() = 0;
  };

  class IElevationImporter
  {
  public:
    virtual ~IElevationImporter() {};

    // If your importer wishes to display progress as it is running, this may
    // be overriden to achieve that.
    virtual IProgress* Progress() { return nullptr; }

    virtual void BeginTile(Point2D LowerBound,
                           Point2D UpperBound,
                           Vector2D CellSize) = 0;

    // DiscardTile will be true if the tile should be thrown away. This will be
    // suggested if the tile was empty.
    virtual void EndTile(int TileIndexX, int TileIndexY, bool DiscardTile) = 0;

    // This sets the value in the current tile, the X and Y are relative to
    // the current tile.
    virtual void SetValue(int X, int Y, double Value) = 0;

    // Flag there being no value, the X and Y are relative to the current tile.
    virtual void FlagNoData(int X, int Y) = 0;
  };

  void RegisterAdditionalTiffTags();
  // Call this function at the start to register the GDAL + GeoTIFF tags
  // for TIFF.

  // Read in the tiles into the given elevation importer grid.
  void ReadViaTiles(TIFF* Tiff, IElevationImporter* Importer);

  // Read in the scan lines into a given importer treating it as a single tile.
  // Ideally, the importer could be queried for a max size and if so then
  // it could be broken up until multiple tiles.
  void ReadViaScanLines(TIFF* Tiff, IElevationImporter* Importer);
}

#endif
