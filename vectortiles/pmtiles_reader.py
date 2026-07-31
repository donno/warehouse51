"""Read fromPMTiles archive file.

The PMTiles is cloud-optimized archives of map tiles.

This relies on https://github.com/developmentseed/async-pmtiles and
the underlying pmtiles library.
"""
# /// script
# dependencies = ["async-pmtiles", "obstore", "protobuf", "skia-python"]
# ///
from async_pmtiles import PMTilesReader
from pmtiles.tile import TileType
from pmtiles.reader import Reader, MmapSource
from obstore.store import HTTPStore, LocalStore

from vectortiles import read_vector_tile, DevelopmentTileVisitor, process_tile
from skia_renderer import render_tile
import asyncio
import pathlib

async def go(store, name: str):
    
    src = await PMTilesReader.open(name, store=store)
    print(type(src))
    bounds = src.bounds
    minzoom, maxzoom = src.minzoom, src.maxzoom
    print(bounds)
    # The alternative is MapLibre Vector Tile.
    if src.tile_type != TileType.MVT:
       raise ValueError(f"Expected MVT Vector Tile got {src.tile_type}")

    #print(await src.metadata())
    data = await src.get_tile(x=3624, y=2472, z=12)
    if data is None:
        raise ValueError("No tile found")
    tile = read_vector_tile(bytes(data))

    #visitor = DevelopmentTileVisitor()
    #process_tile(tile, visitor)
    
    # TODO: See the tile renderer in  skia_renderer
    render_tile(tile, "pmtile_render.png")


def go_sync(tiles):
    with open(tiles, "r+b") as source:
        reader = Reader(MmapSource(source))
        raw_tile = reader.get(x=3624, y=2472, z=12)
        tile = read_vector_tile(raw_tile)
        render_tile(tile, "pmtile_render.png")


if __name__ == "__main__":
    # HTTP
    #store = HTTPStore("https://r2-public.protomaps.com/protomaps-sample-datasets")
    #asyncio.run(go(store, "cb_2018_us_zcta510_500k.pmtiles"))
    # Local file system
    australia = pathlib.Path(r"K:\GeoData\Generated\OpenStreetMap\australia.pmtiles")
    store = LocalStore(australia.parent)
    asyncio.run(go(store, australia.name))

    #go_sync(australia)