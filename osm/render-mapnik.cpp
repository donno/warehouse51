// Render OpenStreetMap tiles using Mapnik.
//
// By default this is set-up to render the tiles of level 4 to 18 (18 is
// probably a little too detailed for starting off).
//
// The key function is render_tile() which takes a tile index with zoom and
// renders a single tile.
//
// For finding the tile numbers/indices se geofabrik which can show a grid
// overlay with the indices.:
// https://tools.geofabrik.de/map/#12/-34.9365/138.5164&type=Geofabrik_Standard&grid=1
//
// Building on Linux:
// g++ -I ~/mapnik/include/  render-mapnik.cpp ~/mapnik/build/out/libmapnik.so.4.0.0 -lboost_program_options
//
// Build on Windows: Use nmake -f Makefile.msvc
// Others will need to tweak the paths to vcpkg.

#include <mapnik/map.hpp>
#include <mapnik/mapnik.hpp>
#include <mapnik/load_map.hpp>
#include <mapnik/agg_renderer.hpp>
#include <mapnik/image.hpp>
#include <mapnik/image_util.hpp>
#include <mapnik/config_error.hpp>
#include <mapnik/datasource_cache.hpp>

#include <boost/program_options.hpp>

#include <filesystem>
#include <string>

// Function declarations.

static mapnik::box2d<double> wgs84_to_mercator(mapnik::box2d<double> box);
static mapnik::coord2d slippy_to_wgs84_corner(int x, int y, int zoom);
static mapnik::box2d<double> slippy_to_wgs84_bounds(int x, int y, int zoom);
static mapnik::coord2i wgs84_to_slippy(mapnik::coord2d wgs84, int zoom);
static mapnik::box2d<int> wgs84_to_slippy(
    mapnik::box2d<double> wgs84, int zoom);

static void render_tiles(
    mapnik::box2d<double> bounding_box,
    mapnik::Map& map,
    const std::filesystem::path& tile_directory,
    std::string name,
    int minimum_zoom = 1,
    int maximum_zoom = 18);
// minimum_zoom must be 1 or greater.
// maximum_zoom must be 18 or less than and is inclusive.

static void render_tile(
    mapnik::Map& map,
    const std::filesystem::path& tile_directory,
    int tile_index_x,
    int tile_index_y,
    int zoom);

// Function defintions.

mapnik::box2d<double> wgs84_to_mercator(mapnik::box2d<double> box)
{
    auto x0 = box.minx();
    auto x1 = box.maxx();
    auto y0 = box.miny();
    auto y1 = box.maxy();

    // lonlat2merc
    // ===========
    // auto dx = clamp(x, -180.0, 180.0);
    // auto dy = clamp(
    //     y, -mapnik::MERC_MAX_LATITUDE, mapnik::MERC_MAX_LATITUDE);
    // x = mapnik::EARTH_RADIUS * radians(dx);
    // y = mapnik::EARTH_RADIUS * std::log(std::tan(radians(90.0 + dy) / 2.0));

    mapnik::lonlat2merc(x0, y0);
    mapnik::lonlat2merc(x1, y1);
    return {x0, y0, x1, y1};
}

mapnik::coord2d slippy_to_wgs84_corner(int x, int y, int zoom)
{
    const double n =
        mapnik::util::pi - mapnik::util::tau * y / (double)(1 << zoom);
    return {
        x / (double)(1 << zoom) * 360.0 - 180,
        180.0 / mapnik::util::pi * atan(0.5 * (exp(n) - exp(-n)))
    };
}

mapnik::box2d<double> slippy_to_wgs84_bounds(int x, int y, int zoom)
{
    return {
        slippy_to_wgs84_corner(x, y, zoom),
        slippy_to_wgs84_corner(x + 1, y + 1, zoom)
    };
}

mapnik::coord2i wgs84_to_slippy(mapnik::coord2d wgs84, int zoom)
{
    double lat_rad = wgs84.y * mapnik::util::pi / 180.0;
    return {
        (int)(floor((wgs84.x + 180.0) / 360.0 * (1 << zoom))),
        (int)(floor((1.0 - asinh(tan(lat_rad)) / mapnik::util::pi) / 2.0 *
                    (1 << zoom)))};
}

mapnik::box2d<int> wgs84_to_slippy(mapnik::box2d<double> wgs84, int zoom)
{
    return {
        wgs84_to_slippy({wgs84.minx(), wgs84.miny()}, zoom),
        wgs84_to_slippy({wgs84.maxx(), wgs84.maxy()}, zoom),
    };
}

void render_tiles(
    mapnik::box2d<double> bounding_box,
    mapnik::Map& map,
    const std::filesystem::path& tile_directory,
    std::string name,
    int minimum_zoom,
    int maximum_zoom)
{
    minimum_zoom = std::max(minimum_zoom, 1);
    maximum_zoom = std::max(maximum_zoom, 18);

    // Start of my creating the directory structure.
    for (int zoom = minimum_zoom; zoom <= maximum_zoom; ++zoom)
    {
        // Create the folder for the zoom level in tile_directory.
        auto zoom_directory = tile_directory / name / std::to_string(zoom);
        std::filesystem::create_directories(zoom_directory);

        // Determine the tile-x and tile-y ranges.
        auto tile_bounds = wgs84_to_slippy(bounding_box, zoom);
        for (int tile_x = tile_bounds.minx(); tile_x <= tile_bounds.maxx();
             ++tile_x)
        {
            std::filesystem::create_directory(
                zoom_directory / std::to_string(tile_x));
        }
    }

    // Next render the tiles.
    //
    // This is where parallelism would help. The idea there is spawn N threads
    // generate list of work for them (i.e the tiles) and they each create a
    // map instance and perform the render.

    // Start of my creating the directory structure.
    for (int zoom = minimum_zoom; zoom <= maximum_zoom; ++zoom)
    {
        // Determine the tile-x and tile-y ranges.
        auto tile_bounds = wgs84_to_slippy(bounding_box, zoom);
        for (int tile_x = tile_bounds.minx();
             tile_x <= tile_bounds.maxx(); ++tile_x)
        {
            for (int tile_y = tile_bounds.miny(); tile_y <= tile_bounds.maxy();
                 ++tile_y)
            {
                render_tile(map, tile_directory / name, tile_x, tile_y, zoom);
            }
        }
    }
}

void render_tile(mapnik::Map& map,
                 const std::filesystem::path& tile_directory,
                 int tile_index_x,
                 int tile_index_y,
                 int zoom)
{
    const auto zoom_directory = tile_directory / std::to_string(zoom);
    const auto filename =
        zoom_directory / std::to_string(tile_index_x) /
        (std::to_string(tile_index_y) + ".png");
    const auto bounds_wgs84 =
        slippy_to_wgs84_bounds(tile_index_x, tile_index_y, zoom);

    // This works because the map projection is in web mercator.
    // However if map.srs() was something else a different transform is needed.

    map.resize(256, 256);
    map.zoom_to_box(wgs84_to_mercator(bounds_wgs84));

    mapnik::image_rgba8 image(256, 256);
    mapnik::agg_renderer<mapnik::image_rgba8> renderer(map, image);
    renderer.apply();
    mapnik::save_to_file(image, filename.string());
}

int main(int argc, const char* argv[])
{
    boost::program_options::options_description description("Allowed options");
    description.add_options()
        ("help", "produce help message")
        ("map-file",
         boost::program_options::value<std::string>()->default_value("mapnik.xml"),
        "the map file in Mapnik XML. This is typically generated from a MML "
        "document (a stylesheet for a map) with CartoCSS.")
        ("output",
         boost::program_options::value<std::string>()->default_value("output"),
        "the directory to output the tiles into.")
        ("fonts",
         boost::program_options::value<std::string>(),
        "the directory to fonts needed by the map style.")
    ;

    boost::program_options::variables_map vm;
    boost::program_options::store(
        boost::program_options::parse_command_line(argc, argv, description),
        vm);
    boost::program_options::notify(vm);

    if (vm.count("help")) {
        std::cout << description << "\n";
        return 1;
    }

    std::filesystem::path map_file(vm["map-file"].as<std::string>());
    if (!std::filesystem::exists(map_file))
    {
        std::cerr << "map file: " << map_file << " does not exist\n";
        return 1;
    }

    std::filesystem::path output(vm["output"].as<std::string>());
    std::filesystem::create_directories(output);

    // Register the image handlers with mapnik.
    // Otherwise warning for "could not initialize reader for: <png file>".
    mapnik::setup(); // Registers the image handlers.

    // Optionally set-up ability to give it a folder containing the fonts and
    // call map.register_fonts

    // Requires conversion rom lat-long (EPSG:4326) to mercator (EPSG: 3857).
    mapnik::box2d<double> bound_wgs84 = {138.54, -34.95, 138.65, -34.88 };
    mapnik::box2d<double> bound_mercator = wgs84_to_mercator(bound_wgs84);
    // Translated via epsg.io
    // {15422202.2545, -4157088.418046, 15434447.39848738, -4147585.557396048 };

    try
    {
        mapnik::datasource_cache::instance().register_datasources("plugins/input");
        mapnik::Map m(256, 256);

        if (vm.count("fonts"))
        {
            m.register_fonts(vm["fonts"].as<std::string>());
        }

        mapnik::load_map(m, map_file.string());

        // Start of rendering a quick overlay / test image.
        m.zoom_to_box(bound_mercator);
        mapnik::image_rgba8 im(256,256);
        mapnik::agg_renderer<mapnik::image_rgba8> ren(m, im);
        ren.apply();
        mapnik::save_to_file(im, (output / "adelaide.png").string());

        render_tiles(bound_wgs84, m, output, "adelaide", 4, 18);

    }
    catch (const mapnik::config_error& error)
    {
        std::cerr << "Configuration error: " <<  error.what() << '\n';
        return 1;
    }
    catch(const std::exception& e)
    {
        std::cerr << e.what() << '\n';
        return 1;
    }


    return 0;
}

#ifdef VARIOUS_TESTING
    {
        // Render a speciifc tile:
        //
        // https://tile.openstreetmap.org/10/906/618.png?lang=en
        render_tile(map, tile_directory / name, 906, 618, 10);
    }

    mapnik::box2d<double> bound_wgs84 = {138.54, -34.95, 138.65, -34.88 };
    mapnik::box2d<double> bound_mercator = wgs84_to_mercator(bound_wgs84);
    std::cout << "WGS84 bound: " << bound_wgs84 << "\n" << "Mercator bound: "
                << bound_mercator << "\n";

    //    auto bounds_wgs84 = slippy_to_wgs84_bounds(906, 618, 10);
    const auto wgs84 = slippy_to_wgs84_corner(906, 618, 10);
    std::cout << wgs84.x << "," << wgs84.y << std::endl;
#endif
