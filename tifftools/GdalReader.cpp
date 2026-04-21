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
// References:
// - https://gdal.org/en/stable/tutorials/raster_api_tut.html
// - https://gdal.org/en/stable/tutorials/raster_dtm_tut.html
//
// Development:
// - apk add gdal-dev g++  # For Alpine
// - g++ GdalReader.cpp -D TIFFTOOLS_WITH_GDAL_READER_MAIN -lgdal -o gdal_reader
// - ./gdal_reader build/vmelev_dem10m_sub_section_tile.tif
//===----------------------------------------------------------------------===/

#include "GdalReader.hpp"

#define TIFFTOOLS_WITHOUT_LIBTIFF
#include "TiffTools.hpp"

#include "gdal_priv.h"

#include <optional>

static TiffTools::Gdal::Bounds QueryBounds(GDALRasterBand *Band) {
  const auto width = Band->GetXSize();
  const auto height = Band->GetYSize();

  double geoTransform[6];
  if (Band->GetDataset()->GetGeoTransform(geoTransform) == CE_None) {
    TiffTools::Gdal::Bounds bounds;
    bounds.originX = geoTransform[0];
    bounds.originY = geoTransform[3] + height * geoTransform[5];
    bounds.cellSizeX = geoTransform[1];
    bounds.cellSizeY = geoTransform[5];
    bounds.width = width * geoTransform[1];
    bounds.height = height * geoTransform[5];
    return bounds;
  }

  fprintf(stderr, "Unable to determine bounds (origin and size).\n");
  return {};
}

static void error_reporter(CPLErr error_class, int error_number,
                           const char *message) {
  fprintf(stderr, "Error (%d) with GDAL occurred: %s\n", error_number, message);
}

static bool validate_bounds(const TiffTools::Point2D &LowerLeft,
                            const TiffTools::Point2D &UpperRight) {
  if (LowerLeft.x > UpperRight.x) {
    fprintf(
        stderr,
        "The X-coordinate of the lower-left is further to the right then the "
        "upper-right: %f vs %f.\n",
        LowerLeft.x, UpperRight.x);
  }

  if (UpperRight.y < LowerLeft.y) {
    fprintf(
        stderr,
        "The Y-coordinate of the upper-right is below the lower-left point: "
        "%f should be smaller than %f.\n",
        LowerLeft.y, UpperRight.y);
  }
  return true;
}

// Allocate the array using GDAL's Common Portability Library.
template <typename T>
static std::unique_ptr<T[], decltype(&::CPLFree)> malloc_array(size_t size) {
  return {(T *)::CPLMalloc(sizeof(T) * size), ::CPLFree};
}

static void output_information(GDALDataset *dataset) {
  double adfGeoTransform[6];
  printf("Driver: %s/%s\n", dataset->GetDriver()->GetDescription(),
         dataset->GetDriver()->GetMetadataItem(GDAL_DMD_LONGNAME));
  printf("Size is %dx%dx%d\n", dataset->GetRasterXSize(),
         dataset->GetRasterYSize(), dataset->GetRasterCount());
  if (dataset->GetProjectionRef() != NULL)
    printf("Projection is `%s'\n", dataset->GetProjectionRef());
  if (dataset->GetGeoTransform(adfGeoTransform) == CE_None) {
    printf("Origin = (%.6f,%.6f)\n", adfGeoTransform[0], adfGeoTransform[3]);
    printf("Pixel Size = (%.6f,%.6f)\n", adfGeoTransform[1],
           adfGeoTransform[5]);
  }

  printf("\nBand information\n");
  GDALRasterBand *band = dataset->GetRasterBand(1);
  int blockXSize, blockYSize;
  band->GetBlockSize(&blockXSize, &blockYSize);
  printf("Block=%dx%d Type=%s, ColorInterp=%s\n", blockXSize, blockYSize,
         GDALGetDataTypeName(band->GetRasterDataType()),
         GDALGetColorInterpretationName(band->GetColorInterpretation()));
  int bGotMin, bGotMax;
  double adfMinMax[2];
  adfMinMax[0] = band->GetMinimum(&bGotMin);
  adfMinMax[1] = band->GetMaximum(&bGotMax);
  if (!(bGotMin && bGotMax))
    GDALComputeRasterMinMax((GDALRasterBandH)band, TRUE, adfMinMax);
  printf("Min=%.3fd, Max=%.3f\n", adfMinMax[0], adfMinMax[1]);
  if (band->GetOverviewCount() > 0)
    printf("Band has %d overviews.\n", band->GetOverviewCount());
  if (band->GetColorTable() != NULL)
    printf("Band has a color table with %d entries.\n",
           band->GetColorTable()->GetColorEntryCount());

  // Offset and scale
  int success = 0;
  if (double offset = band->GetOffset(&success) && success) {
    printf("Raster value offset: %f\n", offset);
  }

  if (double scale = band->GetScale(&success) && success) {
    printf("Raster value scale: %f\n", scale);
  }
}

void TiffTools::Gdal::SetUp() {
  GDALAllRegister();
  CPLSetErrorHandler(error_reporter);
}

void TiffTools::Gdal::ReadViaTiles(const char *Path,
                                   IElevationImporter *Importer) {
  const GDALAccess access = GA_ReadOnly;
  GDALDatasetUniquePtr dataset =
      GDALDatasetUniquePtr(GDALDataset::FromHandle(GDALOpen(Path, access)));
  if (!dataset) {
    fprintf(stderr, "Failed to open dataset at %s\n", Path);
    return;
  }

  GDALRasterBand *band = dataset->GetRasterBand(1);
  int blockWidth, blockHeight;
  band->GetBlockSize(&blockWidth, &blockHeight);

  auto data = malloc_array<float>(blockWidth * blockHeight);

  const auto blockColumnCount = DIV_ROUND_UP(band->GetXSize(), blockWidth);
  const auto blockRowCount = DIV_ROUND_UP(band->GetYSize(), blockHeight);
  const auto height = band->GetYSize();
  const auto bounds = QueryBounds(band);

  auto progress = Importer->Progress();
  if (progress) {
    progress->Start(blockColumnCount * blockRowCount);
  }

  const TiffTools::Point2D origin{bounds.originX, bounds.originY};
  const Vector2D cellSize{bounds.cellSizeX, bounds.cellSizeY * -1};

  // The following is based on the example in GDALRasterBand::ReadBlock().
  //
  // https://gdal.org/en/stable/doxygen/classGDALRasterBand.html#aed60995d0a5ac730d5137fb96fb0b141

  // TODO: Confirm the X,Y values are computed correct and that it
  // shouldn't be subtracting the row.

  // blockRow = 0, means the top most block and blockColumn = 0 means the
  // left most block.
  //
  // Alternative: look at using GDALRasterBand::IterateWindows() which iterates
  // over windows aligned to blocks.
  for (int blockRow = 0; blockRow < blockRowCount; blockRow++) {
    const int tileYOffset = blockRow * blockHeight;

    for (int blockColumn = 0; blockColumn < blockColumnCount; blockColumn++) {
      const int tileXOffset = blockColumn * blockWidth;

      const TiffTools::Point2D lowerBound{
          origin.x + blockWidth * blockColumn,
          origin.y - blockHeight * blockRow,
      };
      const TiffTools::Point2D upperRight{
          origin.x + blockWidth * (blockColumn + 1),
          origin.y - blockHeight * (blockRow + 1),
      };

      if (!validate_bounds(lowerBound, upperRight)) {
        fprintf(stderr, "Bounds were invalid - aborting.\n");
        break;
      }

      Importer->BeginTile(lowerBound, upperRight, cellSize);
      auto result = band->ReadBlock(blockColumn, blockRow, data.get());
      if (result == CE_Failure) {
        fprintf(stderr, "Failed to read block from first band - skipping.\n");
        continue;
      }

      // Compute the portion of the block that is valid for partial edge blocks.
      int validXCount, validYCount;
      band->GetActualBlockSize(blockColumn, blockRow, &validXCount,
                               &validYCount);
      for (int row = 0; row < validYCount; ++row) {
        for (int column = 0; column < validXCount; ++column) {
          Importer->SetValue(tileXOffset + column,
                             tileYOffset + (blockHeight - row),
                             data[column + row * blockWidth]);
        }
      }

      // TODO: If the entire tile was empty then pass discardTile = true.
      const bool discardTile = true;
      Importer->EndTile(blockColumn, blockRow, discardTile);

      if (progress)
        progress->TileProcessed();
    }
  }

  if (progress)
    progress->End();
}

void TiffTools::Gdal::ReadViaScanLines(const char *Path,
                                       IElevationImporter *Importer) {
  const GDALAccess access = GA_ReadOnly;
  GDALDatasetUniquePtr dataset =
      GDALDatasetUniquePtr(GDALDataset::FromHandle(GDALOpen(Path, access)));
  if (!dataset) {
    fprintf(stderr, "Failed to open dataset at %s\n", Path);
    return;
  }

  GDALRasterBand *band = dataset->GetRasterBand(1);
  const auto width = band->GetXSize();
  const auto height = band->GetYSize();
  auto bounds = QueryBounds(band);
  Importer->BeginTile(
      Point2D{bounds.originX, bounds.originY},
      Point2D{bounds.originX + bounds.width, bounds.originY - bounds.height},
      Vector2D{bounds.cellSizeX, bounds.cellSizeY * -1});

  auto progress = Importer->Progress();
  if (progress)
    progress->Start(height);

  auto scanline = malloc_array<float>(width);

  for (int row = 0; row < height; ++row) {
    // Consider BeginAsyncReader / EndAsyncReader.
    auto result = band->RasterIO(GF_Read, 0, row, width, 1, scanline.get(),
                                 width, 1, GDT_Float32, 0, 0);
    if (result == CE_Failure) {
      fprintf(stderr, "Failed to read data from first band.\n");
      break;
    }

    for (int column = 0; column < width; ++column) {
      // TODO: Handle if there was a no-data value there.
      Importer->SetValue(column, height - row - 1, scanline[column]);
    }

    if (progress)
      progress->StripProcessed();
  }

  if (progress)
    progress->End();

  Importer->EndTile(0, 0, false);
}

TiffTools::Gdal::Bounds TiffTools::Gdal::QueryBounds(const char *Path) {
  const GDALAccess access = GA_ReadOnly;
  GDALDatasetUniquePtr dataset =
      GDALDatasetUniquePtr(GDALDataset::FromHandle(GDALOpen(Path, access)));
  if (!dataset) {
    fprintf(stderr, "Failed to open dataset at %s\n", Path);
    return {};
  }

  GDALRasterBand *band = dataset->GetRasterBand(1);
  return QueryBounds(band);
}

// This is a debug aid.
static int output_values(GDALDataset *dataset) {
  GDALRasterBand *band = dataset->GetRasterBand(1);
  const int sizeX = band->GetXSize();
  int blockXSize, blockYSize;
  band->GetBlockSize(&blockXSize, &blockYSize);

  auto scanline = malloc_array<float>(sizeX);

  // TODO: Handle reading the data - this only reads the first line.
  //
  // Consider reading on block boundaries using ReadBlock() and GetBlockSize().
  // Consider BeginAsyncReader / EndAsyncReader.
  for (int row = 0, rowCount = band->GetYSize(); row < rowCount; ++row) {
    auto result = band->RasterIO(GF_Read, 0, 0, sizeX, 1, scanline.get(), sizeX,
                                 1, GDT_Float32, 0, 0);
    if (result == CE_Failure) {
      fprintf(stderr, "Failed to read data from first band.\n");
      return 3;
    }

    for (int i = 0; i < sizeX; ++i) {
      printf("%f ", scanline[i]);
    }
    printf("\n");
    break;
  }

  return 0;
}

class ElevationPrinter : public TiffTools::IElevationImporter {
  void BeginTile(TiffTools::Point2D LowerBound, TiffTools::Point2D UpperBound,
                 TiffTools::Vector2D CellSize) override {}
  void EndTile(int TileIndexX, int TileIndexY, bool DiscardTile) override {};
  void FlagNoData(int X, int Y) override {}

  void SetValue(int X, int Y, double Value) { printf("%f ", Value); }
};

#ifdef TIFFTOOLS_WITH_GDAL_READER_MAIN
int main(int argc, const char *argv[]) {
  if (argc != 2) {
    printf("Missing path to the DEM file.\n");
    return 2;
  }
  const char *filename = argv[1];

  TiffTools::Gdal::SetUp();
#if 1
  ElevationPrinter importer;
  // TiffTools::Gdal::ReadViaScanLines(filename, &importer);
  TiffTools::Gdal::ReadViaTiles(filename, &importer);

  const auto bounds = TiffTools::Gdal::QueryBounds(filename);
  printf("\nOrigin: %f, %f. Cell size: %f, %f\n", bounds.originX,
         bounds.originY, bounds.cellSizeX, bounds.cellSizeY);
  return 0;
#else
  const GDALAccess access = GA_ReadOnly;
  GDALDatasetUniquePtr dataset =
      GDALDatasetUniquePtr(GDALDataset::FromHandle(GDALOpen(filename, access)));
  if (!dataset) {
    return 3;
  }
  output_information(dataset.get());
  return output_values(dataset.get());
#endif
}
#endif
