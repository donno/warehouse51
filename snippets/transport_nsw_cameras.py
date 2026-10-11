"""Show location of traffic cameras for New South Wales, Australia.

Requires API key from https://opendata.transport.nsw.gov.au
"""

# /// script
# dependencies = [
#   "geojson",
#   "requests",
# ]
# ///
import argparse
import dataclasses
import typing

import geojson
import requests


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


def cameras(*, api_key: str) -> list[Camera]:
    """Return the cameras from Transport New South Wales API."""
    response = requests.get(
        "https://api.transport.nsw.gov.au/v1/live/cameras",
        headers={
            "Authorization": f"apiKey {api_key}",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    features = geojson.loads(response.content)

    # The rights could be queried with features["rights"] and included with
    # each camera.

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


def main() -> None:
    """Entry point for printing out details about the cameras."""
    parser = argparse.ArgumentParser(
        "Show location of traffic cameras for NSW",
    )
    parser.add_argument("api_key")
    arguments = parser.parse_args()
    for camera in cameras(api_key=arguments.api_key):
        print(camera)


if __name__ == "__main__":
    main()
