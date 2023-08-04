"""Produces a command/shell script to convert PNG to Geo-referenced TIFF.

It also produces a command to call out gdal_merge.py which will take the TIFFs
and create a single TIFF from it and if there are too many TIFFs it will write
a file containing the list.

TODO:
Improve this so it doesn't have to create the TIFF from the PNG so instead
create a VRT to associate the bounds/coordinate system with the PNGsand treat
it as a single file already.
"""

import argparse
import math
import os


OUTPUT_PATH_TEMPLATE = "{output_path_base}\\{zoom}\\{x}\\{y}.tif"


def tile_edges(x: int, y: int, zoom: int):
    """Convert from tile indices to WGS84 coordinates."""

    def _to_wgs84(x: int, y: int, zoom: int):
        n = math.pi - math.tau * y / (1 << zoom)
        return (
            x / (1 << zoom) * 360.0 - 180.0,
            180.0 / math.pi * math.atan(0.5 * (math.exp(n) - math.exp(-n))),
        )

    lon1, lat1 = _to_wgs84(x, y, zoom)
    lon2, lat2 = _to_wgs84(x + 1, y + 1, zoom)
    return (lon1, lat1, lon2, lat2)


def tiles(base_directory, zoom: int):
    """Return the tiles at the given zoom in the base directory.

    Each item gives (path,  x, ,y ,z).
    """
    for path in os.scandir(os.path.join(base_directory, str(zoom))):
        x = int(os.path.basename(path.path))
        for tile in os.scandir(path):
            y = int(os.path.splitext(os.path.basename(tile))[0])
            yield tile.path, (x, y)


def convert(base_directory, zoom: int, output_directory) -> list:
    """Print commands to convert PNG to geo-references TIFFs.

    Returns the paths of the geo-references TIFFs.
    """
    outputs = []
    for path, (x, y) in tiles(base_directory, zoom):
        bounds = tile_edges(x, y, zoom)
        output_path = OUTPUT_PATH_TEMPLATE.format(
            output_path_base=output_directory, zoom=zoom, y=y, x=x
        )

        # Previously  -expand rgb
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        print(
            "gdal_translate -a_srs EPSG:4326 -a_ullr "
            + " ".join(str(b) for b in bounds)
            + " "
            + path
            + " "
            + output_path
        )
        outputs.append(output_path)

    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate script to use gdal_translate and gdal_merge to "
        "geo-reference tiles produced from OSM and create a single TIFF from "
        "them. The script produced calls out to GDAL tools.",
    )
    parser.add_argument(
        "source_tiles",
        help="The path to the directory containing the tiles as PNGs. "
        "Since gdal_translate will be called this could be any raster format "
        "it supports as long as the tiles use slippy map convention of "
        " zoom/x/y.<ext>.",
        nargs="?",
        default="G:\\GeoData\\Generated\\tiles_adelaide_2023",
    )
    parser.add_argument(
        "--zoom",
        type=int,
        help="The zoom level of interest.",
        default=17,
        # 12 is a good zoom to test for Adelaide as it has 4 tiles (2x2).
    )

    parser.add_argument(
        "--output_directory",
        help="The path to write out the geo-referenced TIFFs",
        default="G:\\GeoData\\Generated\\tiles_adelaide_tiff",
    )

    arguments = parser.parse_args()
    outputs = convert(
        arguments.source_tiles, arguments.zoom, arguments.output_directory
    )

    # Another way to do the following is:
    # python -c "__import__('pkg_resources').run_script('GDAL', 'gdal_merge.py')"
    # However, that may be short-lived as pkg_resources is deprecated.
    #
    # Alternatively, use gdalbuildvrt to create a VRT that references each tile
    # and then use gdal_translate on the resulting VRT.

    merge_command = [
        r"C:\Users\Donno\.conda\envs\geo_env\python.exe",
        r"C:\Users\Donno\.conda\envs\geo_env\Scripts\gdal_merge.py",
        "-o",
        os.path.join(
            arguments.output_directory,
            "adelaide_{zoom}.tif".format(zoom=arguments.zoom),
        ),
    ]

    if len(outputs) > 50:
        option_file = os.path.join(
            arguments.output_directory,
            "tiff_list_{zoom}.txt".format(zoom=arguments.zoom),
        )
        merge_command.extend(["--optfile", option_file])

        with open(option_file, "w") as writer:
            for line in outputs:
                writer.write(line + "\n")
    else:
        merge_command.extend(outputs)

    print(" ".join(merge_command))
