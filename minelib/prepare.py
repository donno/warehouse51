"""Prepares the data sets from Universidad Adolfo Ibañez.

https://mansci-web.uai.cl/minelib/Datasets.xhtml
"""

import asyncio
import urllib.parse
import requests
import aiohttp
import aiofiles
import pathlib
from bs4 import BeautifulSoup

DATASET_URI = "https://mansci-web.uai.cl/minelib/Datasets.xhtml"


def download_urls() -> list[str]:
    response = requests.get(DATASET_URI)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    links = [
        urllib.parse.urljoin(DATASET_URI, anchor["href"])
        for anchor in soup.find_all("a")
        if not anchor["href"].endswith(".xhtml")
    ]

    return [link for link in links if "minelib" in link]


async def download_file(
    session: aiohttp.ClientSession, url: str, destination: pathlib.Path
) -> pathlib.Path:
    """Download the file.

    -------
    Execute the downloads asynchronously.

    >>> loop = asyncio.get_event_loop()
    >>> loop.run_until_complete(create_routes(frame, project))
    """
    response = await session.request(method="GET", url=url)
    response.raise_for_status()
    filename = pathlib.PurePath(urllib.parse.urlparse(url).path).name
    chunk_size = 1024 * 4
    async with aiofiles.open(destination / filename, mode="wb") as writer:
        async for chunk in response.content.iter_chunked(chunk_size):
            if chunk:
                await writer.write(chunk)
    return destination / filename


async def download_files(urls, destination: pathlib.Path):
    """Download the files

    Examples
    -------
    Execute the downloads asynchronously.

    >>> loop = asyncio.get_event_loop()
    >>> loop.run_until_complete(download_files(urls))
    """
    async with aiohttp.ClientSession() as session:
        tasks = [download_file(session, url, destination) for url in urls]
        return await asyncio.gather(*tasks)


if __name__ == "__main__":
    urls = download_urls()
    # print("\n".join(urls))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_files(urls[:5], pathlib.Path.cwd() / "data"))
