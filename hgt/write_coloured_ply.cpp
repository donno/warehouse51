//===----------------------------------------------------------------------===//
//
// NAME         : write_coloured_ply
// PURPOSE      : Write with per-vertex colors based on height
// COPYRIGHT    : Public Domain / https://creativecommons.org/public-domain/cc0/
// AUTHORS      : Kimi 2.6 (Large Language Model).
//===----------------------------------------------------------------------===//

#include "triangulator_kimi.hpp"

#include <algorithm>
#include <fstream>
#include <iomanip>
#include <numeric>
#include <sstream>
#include <string>

using Triangulator::Kimi::DEMTriangulationResult;

/**
 * Writes a DEM triangulation result to an ASCII PLY file with vertex colors.
 * Colors are mapped from elevation (z) using a simple terrain colormap.
 *
 * @param filename   Output file path
 * @param result     The triangulation result
 * @param zMin       Minimum elevation for color mapping (auto if NaN)
 * @param zMax       Maximum elevation for color mapping (auto if NaN)
 * @return           true on success, false on failure
 */
bool writePLYWithColors(const std::string& filename,
                        const DEMTriangulationResult& result,
                        double zMin = std::numeric_limits<double>::quiet_NaN(),
                        double zMax = std::numeric_limits<double>::quiet_NaN()) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        return false;
    }

    // Auto-compute z range if not provided
    if (std::isnan(zMin) || std::isnan(zMax)) {
        zMin = std::numeric_limits<double>::infinity();
        zMax = -std::numeric_limits<double>::infinity();
        for (const auto& p : result.points) {
            zMin = std::min(zMin, p.z);
            zMax = std::max(zMax, p.z);
        }
    }

    const double zRange = zMax - zMin;
    const size_t numPoints = result.points.size();
    const size_t numTriangles = result.triangles.size();

    // PLY header with color properties
    file << "ply\n";
    file << "format ascii 1.0\n";
    file << "element vertex " << numPoints << "\n";
    file << "property float x\n";
    file << "property float y\n";
    file << "property float z\n";
    file << "property uchar red\n";
    file << "property uchar green\n";
    file << "property uchar blue\n";
    file << "element face " << numTriangles << "\n";
    file << "property list uchar int vertex_indices\n";
    file << "end_header\n";

    // Simple terrain colormap: blue (low) -> green -> brown -> white (high)
    auto heightToColor = [](double z, double zMin, double zRange)
        -> std::tuple<unsigned char, unsigned char, unsigned char> {
        if (zRange < 1e-6) return {128, 128, 128};

        double t = std::clamp((z - zMin) / zRange, 0.0, 1.0);
        unsigned char r, g, b;

        if (t < 0.25) {         // Deep water to shallow water
            double s = t / 0.25;
            r = 0;
            g = static_cast<unsigned char>(s * 100);
            b = static_cast<unsigned char>(128 + s * 127);
        } else if (t < 0.5) {   // Shallow water to grass
            double s = (t - 0.25) / 0.25;
            r = static_cast<unsigned char>(s * 34);
            g = static_cast<unsigned char>(100 + s * 105);
            b = static_cast<unsigned char>(255 - s * 155);
        } else if (t < 0.75) {  // Grass to rock
            double s = (t - 0.5) / 0.25;
            r = static_cast<unsigned char>(34 + s * 102);
            g = static_cast<unsigned char>(205 - s * 80);
            b = static_cast<unsigned char>(100 - s * 80);
        } else {                // Rock to snow
            double s = (t - 0.75) / 0.25;
            r = static_cast<unsigned char>(136 + s * 119);
            g = static_cast<unsigned char>(125 + s * 130);
            b = static_cast<unsigned char>(20 + s * 235);
        }

        return {r, g, b};
    };

    // Write vertices with colors
    for (const auto& p : result.points) {
        auto [r, g, b] = heightToColor(p.z, zMin, zRange);
        file << std::fixed << std::setprecision(6)
             << p.x << " " << p.y << " " << p.z << " "
             << static_cast<int>(r) << " "
             << static_cast<int>(g) << " "
             << static_cast<int>(b) << "\n";
    }

    // Write faces
    for (const auto& tri : result.triangles) {
        file << "3 " << tri.v0 << " " << tri.v1 << " " << tri.v2 << "\n";
    }

    file.close();
    return file.good();
}

