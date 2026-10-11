"""Show location of traffic cameras for New South Wales, Australia.

Requires API key from https://opendata.transport.nsw.gov.au
"""

# /// script
# dependencies = [
#   "geojson",
#   "requests",
#   "aiohttp",
# ]
# ///
import argparse
import asyncio
import dataclasses
import typing

import aiohttp
import geojson
import requests

API_CAMERA_URL = "https://api.transport.nsw.gov.au/v1/live/cameras"
"""The URL to the API for querying the traffic cameras."""


class CameraProperties(typing.TypedDict):
    """Properties of a traffic camera."""

    region: str
    title: str
    view: str
    direction: str
    href: str


@dataclasses.dataclass
class Camera:
    """Represents a traffic camera."""

    identifier: str
    """A unique identifier for the camera."""

    latitude: float
    """The north-south position of a point on the surface of the Earth."""

    longitude: float
    """The east-west position of a point on the surface of the Earth."""

    properties: CameraProperties
    """Properties of the camera."""


def _response_to_cameras(content: str) -> list[Camera]:
    """Decode the response from the HTTP API request to a list of cameras."""
    # The rights could be queried with features["rights"] and included with
    # each camera.
    features = geojson.loads(content)
    cameras: list[Camera] = []
    for feature in features["features"]:
        if feature["type"] != "Feature":
            continue
        feature_id = feature["id"]
        geometry = feature["geometry"]
        geometry_type = geometry["type"]
        if geometry_type != "Point":
            message = (
                "Geometry was expected to be a point for feature "
                f"{feature_id} but was {geometry_type}."
            )
            raise ValueError(message)

        properties = feature["properties"]
        (
            lat,
            long,
        ) = geometry["coordinates"]
        cameras.append(Camera(feature_id, lat, long, properties))
    return cameras


def fetch_cameras(*, api_key: str) -> list[Camera]:
    """Return the cameras from Transport New South Wales API."""
    response = requests.get(
        API_CAMERA_URL,
        headers={
            "Authorization": f"apiKey {api_key}",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return _response_to_cameras(response.content)


async def fetch_cameras_async(*, api_key: str) -> list[Camera]:
    """Return the cameras from Transport New South Wales API."""
    async with aiohttp.ClientSession() as session, session.get(
        API_CAMERA_URL,
        headers={
            "Authorization": f"apiKey {api_key}",
        },
    ) as response:
        response.raise_for_status()
        return _response_to_cameras(await response.text())


def main() -> None:
    """Entry point for printing out details about the cameras."""
    parser = argparse.ArgumentParser(
        "Show location of traffic cameras for NSW",
    )
    parser.add_argument("api_key")
    parser.add_argument(
        "--async",
        dest="async_requests",
        action="store_true",
        # This will matter more when we can fetch multiple cameras images at
        # once.
        help="Issue the request asynchronously",
    )
    arguments = parser.parse_args()

    if arguments.async_requests:
        cameras = asyncio.run(fetch_cameras_async(api_key=arguments.api_key))
    else:
        cameras = fetch_cameras(api_key=arguments.api_key)

    for camera in cameras:
        print(camera)


if __name__ == "__main__":
    main()
