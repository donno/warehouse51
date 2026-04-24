//===----------------------------------------------------------------------===//
//
// NAME         : triangulator_kimi
// NAMESPACE    : Triangulator.Kimi
// PURPOSE      : Provide function for producing a triangulation from a DEM.
// COPYRIGHT    : Public Domain / https://creativecommons.org/public-domain/cc0/
// AUTHORS      : Kimi 2.6, driven by Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides functions for traignulation
//
//===----------------------------------------------------------------------===//

#include <string>
#include <vector>

namespace Triangulator
{
    namespace Kimi
    {
        struct Point {
            double x, y, z;
            int row, col; // Source DEM coordinates (for reconstruction/debugging)
            size_t index; // Index in output points array

            Point(double x_, double y_, double z_, int r, int c, size_t idx)
                : x(x_), y(y_), z(z_), row(r), col(c), index(idx) {}
        };

        struct Triangle {
            size_t v0, v1, v2;      // Indices into points array
            double error;           // Geometric error metric for simplification

            Triangle(size_t a, size_t b, size_t c)
                : v0(a), v1(b), v2(c), error(0.0) {}
        };

        struct DEMTriangulationResult {
            std::vector<Point> points;
            std::vector<Triangle> triangles;
            size_t peak_memory_bytes;
        };

        // Triangulate a full DEM with incremental simplification.
        //
        // heights: column-major array of size rows * cols
        //          (i.e., heights[row * cols + col])
        DEMTriangulationResult triangulateDEM(
            int rows, int cols,
            const double* heights,
            double cell_size_x = 1.0,
            double cell_size_y = 1.0,
            size_t max_active_rows = 64,
            double simplification = 0.5);

        // Writes a DEM triangulation result to an ASCII PLY file.
        // filename: Output file path (e.g., "terrain.ply")
        // result:   The triangulation result from triangulateDEM()
        //
        // Return true on success and false on failure.
        bool writePLY(const std::string& filename, const DEMTriangulationResult& result);
  }
}

