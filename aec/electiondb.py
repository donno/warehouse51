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
import argparse
import datetime
import pathlib

# Third party imports
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

# Our imports
import preload
import mediafeed

SCRIPT_DIRECTORY = pathlib.Path(__file__).parent


async def import_preload_event(
    preload_location: pathlib.Path, database: AsyncIOMotorDatabase
) -> None:
    """Import the event preload information into the database."""
    event, authority, *elections = preload.load_event(preload_location)

    await database.events.insert_one(
        {
            "authority": authority,
            **event,
        }
    )

    all_elections = []
    all_contests = []

    for election, contests in elections:
        all_elections.append({**election, "event": event["id"]})

        for contest in contests:
            contest["_id"] = f'{event["id"]}-{election["id"]}-{contest["id"]}'
            contest.update(
                {
                    "event": event["id"],
                    "election": election["id"],
                }
            )
            all_contests.append(contest)

    await database.elections.insert_many(all_elections)
    await database.contests.insert_many(all_contests)


async def import_preload_results(
    preload_location: pathlib.Path, database: AsyncIOMotorDatabase
) -> None:
    """Import the results from preload information into the database.

    This is essentially the votes the candidates received from past election
    with all zeroes for the votes for the current election.
    """
    collection_names = await database.list_collection_names()
    if not any(name == "results" for name in collection_names):
        await database.create_collection(
                "results",
                timeseries={
                    "timeField": "timestamp",
                    "metaField": "eventContest",
                },
            )

    for election, contests in preload.load_results_from_path(preload_location):
        contests_to_save = _convert_contests(election, contests)
        await database.results.insert_many(contests_to_save)


async def import_preload(
    preload_location: pathlib.Path, database: AsyncIOMotorDatabase
) -> None:
    """Import the preload information into the database.

    This loads the polling districts at this time.
    """
    await import_preload_results(preload_location, database)

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

    all_candidates = []
    for event, election, contest, candidate in preload.load_candidates(
        preload_location
    ):
        all_candidates.append(candidate.to_dict())
        id_parts = [
            event["id"],
            election["id"],
            contest["id"],
            candidate.identifier,
        ]
        all_candidates[-1].update(
            {
                "_id": "-".join(id_parts),
                "event": event["id"],
                "election": election["id"],
                "contest": contest["id"],
            }
        )

    await database.candidates.insert_many(all_candidates)

    await import_preload_event(preload_location, database)

    await import_preload_results(preload_location, database)


async def import_results(
    results_directory: pathlib.Path, database: AsyncIOMotorDatabase
) -> None:
    """Import the results  into the database.

    The results directory is expected to contain ZIP files, with an XML file
    containing the results for that point in time.
    """
    # result_zips = [
    #     path
    #     for path in results_directory.iterdir()
    #     if path.suffix == ".zip"
    # ]
    # result_zip = next(iter(result_zips))

    for eml in mediafeed.emls(results_directory):
        for election, contests in preload.load_results(eml):
            contests_to_save = _convert_contests(election, contests)
            await database.results.insert_many(contests_to_save)

    #print(result_zip)


def _convert_contests(election: dict, contests) -> list[dict]:
    """Convert the contests to JSON for the database."""
    timestamp = datetime.datetime.fromisoformat(election["created"])

    contests_to_save = []
    for contest in contests:
        contest["timestamp"] = timestamp
        contest["eventId"] = election["event"]["id"]
        contest["contestId"] = contest.pop("id")
        contest["eventContest"] =  contest["eventId"] + "-" + contest["contestId"]
        contests_to_save.append(contest)
    return contests_to_save


PRELOAD = (
    SCRIPT_DIRECTORY
    / "data"
    / "aec-mediafeed-Detailed-Preload-27966-20220518111207.zip"
)

DIRECTORY = pathlib.Path("Y:\\24310_2019_Election\\Detailed_Verbose")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate a MongoDB database with election data.",
    )
    parser.add_argument("--db-host", type=str, default="localhost",
                        help="The host name for the MongoDB server to use.")
    parser.add_argument("--db-port", type=int, default=27017,
                        help="The port for the MongoDB server to use.")

    arguments = parser.parse_args()
    client = motor.motor_asyncio.AsyncIOMotorClient(
        arguments.db_host,
        arguments.db_port,
    )
    db = client.test_database
    db = client["aec"]

    loop = client.get_io_loop()
    # Preload might be better off in a sqlite database as the data is uniform
    # a poling district always has set number of fields so do the polling place.
    loop.run_until_complete(import_preload(PRELOAD, db))


    # Import past election results.
    #
    # This will import contests which have no changes since the previous entry
    # that is to say, no additional votes have been tallied. It may be better
    # to improve this so compares entries with the previous or next entry
    # before saving them.
    loop.run_until_complete(import_results(DIRECTORY, db))
