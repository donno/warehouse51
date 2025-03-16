"""Provides access to a database for storing the election results.

MongoDB is being evaluated for this purpose.

Development
-----------
- podman pull docker.io/mongodb/mongodb-community-server:latest
- podman run --rm  -it -p 27017:27017 docker.io/mongodb/mongodb-community-server:latest
  - Data won't persist - Data will be persisted if /data/db is mapped to volume.
  - This assumes monodb isn't running on the host or via another container on
    the default port.

For web based interface to integrate the data stored:
- podman pull quay.io/lib/mongo-express
- podman run --rm -it -p 28017:8081 ^
    -e ME_CONFIG_MONGODB_URL=mongodb://10.88.0.3:27017  quay.io/lib/mongo-express
  - The IP will change depending on what was assigned to the container above.


"""

# Standard library imports
import pathlib

# Third party imports
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

# Our imports
import preload

SCRIPT_DIRECTORY = pathlib.Path(__file__).parent

DEFAULT_MONGODB_PORT = 27017
"""The default port for MongoDB"""


async def import_preload(preload_location: pathlib.Path,
                         database: AsyncIOMotorDatabase) -> None:
    """Import the preload information into the database.

    This loads the polling districts at this time.
    """

    def _add_district_id(place: dict, district_id: str) -> dict:
        """Add the identifier for the district to the place."""
        place["districtId"] = district_id
        return place

    districts = []
    all_places = []
    for district, places in preload.load_polling_districts(preload_location):
        districts.append(district.to_dict())
        districts[-1]["_id"] = districts[-1].pop("id")
        all_places.extend(
            _add_district_id(place.to_dict(), district.identifier) for place in places
        )

    await database.districts.insert_many(districts)
    await database.places.insert_many(all_places)

    # TOOD: Load the elections, this is in the events file.
    # TODO: Load the contents

    all_candidates = []
    for election, contest, candidate in preload.load_candidates(
            preload_location):
        all_candidates.append(candidate.to_dict())
        all_candidates[-1]["_id"] = all_candidates[-1].pop("id")
    await database.candidates.insert_many(all_candidates)


PATH = (
    SCRIPT_DIRECTORY
    / "data"
    / "aec-mediafeed-Detailed-Preload-27966-20220518111207.zip"
)


if __name__ == "__main__":
    client = motor.motor_asyncio.AsyncIOMotorClient(
        "localhost",
        DEFAULT_MONGODB_PORT,
    )
    db = client.test_database
    db = client["aec"]

    loop = client.get_io_loop()
    # Preload might be better off in a sqlite database as the data is uniform
    # a poling district always has set number of fields so do the polling place.
    loop.run_until_complete(import_preload(PATH, db))
