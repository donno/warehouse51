# Notes
# - There is a data sets for converting LGA from one year to another.
#   https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/correspondences
#   These CSV are also userful as they turn the codes into names.
#
# https://asgs.linked.fsdf.org.au/dataset/asgsed3
#
import enum
import os

import pandas


class GeographicStructures(enum.Enum):
    """

    Statistical Area Level 1 (SA1) is the second smallest geographic area.

    Mesh Blocks are the smallest geographical area defined by the ABS.

    See https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/latest-release

    Data https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files

    The Australian Bureau of Statistics (ABS) main structures are as follows:
    - Australia
    - STE
    - SA4 (on bar with this area is GCCSA)
    - SA3
    - SA2
    - SA1
    - Mesh Blocks

    The others are either non-ABS or different ways ot representing the data
    for particular purposes by the bureau.
    """

    GCCSA = 0   # Greater Capital City Statistical Areas (GCCSA)

    #  Statistical Areas Level 1 to 4
    SA1 = 1   # Statistical Areas Level 1 (200 to 800 people)
    SA2 = 2   # Level 2 (3,000, 25,000 people)
    SA3 = 3   # Level 3 (30,000, 130,000 people)
    SA4 = 4   # Level 4 (Most are over 100,000 people)
    CED = 5   # Commonwealth Electoral Divisions
    LGA = 6   # Local Government Areas
    POA = 7   # Postal Areas
    SED = 8   # State Electoral Divisions
    SAL = 9   # Suburbs and Localities (previously State Suburbs)
    SOS = 10   # Section of State
    SOSR = 11  # Section of State Ranges
    STE = 12   # States and Territories
    SUA = 13   # Significant Urban Areas
    UCL = 14   # Urban Centre and Locality


SOURCE_DIRECTORY = (
    r'G:\GeoData\Extracted\ABS\GCP\2021 Census GCP All Geographies for SA'
)


def find_geographics(directory):

    name_to_enumerant = {
        enumerant.name: enumerant for enumerant in GeographicStructures
    }

    for entry in os.scandir(directory):
        if entry.is_dir():
            yield name_to_enumerant[entry.name], entry.path


def find_geographics_by_state(directory):
    """Find the data of geographic structures by state (or territory).

    For the 2021 Census data the directory layout was as follows:
        $DATA/<GeographicStructures>/<State>
    Fort example:
        $DATA/LGA/SA - Local Government Areas for the state of South Australia.

    Data will be in the form (GeographicStructures, State, path)
    """
    name_to_enumerant = {
        enumerant.name: enumerant for enumerant in GeographicStructures
    }

    for entry in os.scandir(directory):
        if not entry.is_dir():
            continue

        for sub_entry in os.scandir(entry.path):
            if not sub_entry.is_dir():
                continue

            yield name_to_enumerant[entry.name], sub_entry.name, sub_entry.path


# https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/LGA_2021_AUST_GDA2020_SHP.zip

if __name__ == '__main__':
    for geo, state, path in find_geographics_by_state(SOURCE_DIRECTORY):
        if geo != GeographicStructures.LGA:
            continue

        print(geo, state, path)
        for entry in os.scandir(path):
            frame = pandas.read_csv(entry.path)
            break
