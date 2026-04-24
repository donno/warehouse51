//===----------------------------------------------------------------------===//
//
// NAME         : hgt_to_mesh
// NAMESPACE    : HGT
// PURPOSE      : Provide function for converting HGT file to 3D mesh.
// COPYRIGHT    : (c) 2026 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Provides functions for taking a HGT (height) files which
//                are a data file of the Shuttle Radar Topography Mission
//                (SRTM) and producing a 3D mesh (also known as triangulation)
//                from it.
// STATUS       : Incomplete -Takes too long.
//
// The resulting 3D mesh should not simply contain 3601 * 3601 points (or 1201
// by 1202 for STRM3) and should be simplfied.
//
// Ideals:
// - Dual Contouring
// - Poisson surface reconstruction.
// - Fowler and Little Algorithm - https://dl.acm.org/doi/10.1145/965103.807444
// - Delaunay Triangulation - Using a Uniform grid
//   https://bojianwu.github.io/gsoc2016/week_6/triangulation.pdf
// - https://en.wikipedia.org/wiki/Bowyer%E2%80%93Watson_algorithm
// - https://en.wikipedia.org/wiki/Lloyd%27s_algorithm
//
// Trial:
// - Use large lanage model (LLM) such as Kimi 2.6 to produce an algorithm.
//   The algorithm is implemented in triangulator_kimi.cpp.
//
//===----------------------------------------------------------------------===//

#include "hgt.hpp"
#include "triangulator_kimi.hpp"

#include <filesystem>
#include <iostream>
#include <vector>

int main(int argc, const char* argv[])
{
    try
    {
        const char* filename = (argc > 1) ? argv[1] : "N03W074.hgt";
        const auto format = HGT::IdentifyHgtFile(filename);
        const auto [latitude, longitude] =
            HGT::LocationFromHgtName(filename);
        std::cout << latitude << ", " << longitude << std::endl;

        // The format has how many rows/columns there are.
        const auto size = static_cast<int>(format);

        std::vector<double> dem;
        dem.reserve(size * size);
        HGT::ForEachHeight(
            filename,
            [&dem](auto Height)
            {
                dem.push_back(Height);
            });

        // TODO: Provide an overload of triangulateDEM where it can sample
        // the point.
        const auto result = Triangulator::Kimi::triangulateDEM(
            size, size, dem.data(),
            1.0, 1.0,           // cell sizes - its either 1 or 3 arc-seconds.
            1024,                 // max active rows
            0.5                 // triangle reduction target
        );

        std::filesystem::path output(filename);
        output.replace_extension(".ply");
        writePLY(output.string().c_str(), result);
    }
    catch (const std::runtime_error& Error)
    {
        std::cerr << Error.what() << std::endl;
        return 1;
    }
    return 0;
}

