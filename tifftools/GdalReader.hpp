//===----------------------------------------------------------------------===//
//
// NAME         : GDAL Reader
// NAMESPACE    : TiffTools.Gdal
// PURPOSE      : Uses GDAL for working with TIFF files.
// COPYRIGHT    : (c) 2026 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides tools for working with TIFF files which represent
//                digital elevation models, that is to say not photographs.
//
// This depends on the third party library known as GDAL, which is quite large.
//
//===----------------------------------------------------------------------===/

namespace TiffTools
{
  class IElevationImporter;

  namespace Gdal
  {
    // Read in the tiles into the given elevation importer grid.
    void ReadViaTiles(const char* Path, IElevationImporter *Importer);

    // Read in the scan lines into a given importer treating it as a single tile.
    // Ideally, the importer could be queried for a max size and if so then
    // it could be broken up until multiple tiles.
    void ReadViaScanLines(const char* Path, IElevationImporter *Importer);
  }
}
