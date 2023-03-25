"""Work with ABS boundaries

Information
https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/latest-release

Data:
https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files
"""

import argparse
import os
import zipfile

import fiona
import geopandas
import requests

import abs

BASE_URI = 'https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files'

# https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files/AUS_2021_AUST_SHP_GDA2020.zip

DATA_2021 = {
    'Australia': f'{BASE_URI}/AUS_2021_AUST_SHP_GDA2020.zip',  # I.e 'Country'
    'MeshBlock': f'{BASE_URI}/SA1_2021_AUST_SHP_GDA2020.zip',
    abs.GeographicStructures.SA1: f'{BASE_URI}/SA1_2021_AUST_SHP_GDA2020.zip',
    abs.GeographicStructures.SA2: f'{BASE_URI}/SA2_2021_AUST_SHP_GDA2020.zip',
    abs.GeographicStructures.SA3: f'{BASE_URI}/SA3_2021_AUST_SHP_GDA2020.zip',
    abs.GeographicStructures.SA4: f'{BASE_URI}/SA4_2021_AUST_SHP_GDA2020.zip',
    abs.GeographicStructures.GCCSA: f'{BASE_URI}/GCCSA_2021_AUST_SHP_GDA2020.zip',
    abs.GeographicStructures.STE: f'{BASE_URI}/STE_2021_AUST_SHP_GDA2020.zip',

    # Non ABS Structures
    abs.GeographicStructures.CED: f'{BASE_URI}/CED_2021_AUST_GDA2020_SHP.zip',
    abs.GeographicStructures.LGA: f'{BASE_URI}/LGA_2021_AUST_GDA2020_SHP.zip',
    abs.GeographicStructures.POA: f'{BASE_URI}/POA_2021_AUST_GDA2020_SHP.zip',
    abs.GeographicStructures.SED: f'{BASE_URI}/SED_2021_AUST_GDA2020_SHP.zip',
    abs.GeographicStructures.SAL: f'{BASE_URI}/SAL_2021_AUST_GDA2020_SHP.zip',
}

def download(source_url: str, download_directory, filename=None):
    """Download a file to a given path derivign filename from uri if needed."""
    if not filename:
        filename = source_url.rpartition('/')[-1]

    destination = os.path.join(download_directory, filename)
    response = requests.get(source_url, stream=True)
    response.raise_for_status()

    # If possible derive the filename from the response. For the ABS data
    # it doesn't seem to return the filename.
    # for k, v in response.headers.items():
    #     print(k, v)

    if os.path.isfile(destination):
        # Already downloaded.
        return destination

    with open(destination, 'wb') as output:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                output.write(chunk)
    return destination


def extract(zip, extraction_Location):
    """Extract the specified ZIP file into extraction_location."""
    name = os.path.splitext(os.path.basename(zip))[0]
    destination = os.path.join(extraction_Location, name)

    if os.path.isdir(destination) and os.listdir(destination):
        # TODO: Extract to temp folder then rename once successful so this
        # doesn't get tripped up if it is partially extracted.
        return destination

    with zipfile.ZipFile(zip) as opened_zip:
        opened_zip.extractall(destination)

    return destination


def convert_boundary_to_geojson(extracted_location, generated_location):
    # This may need the ability to apply simplification to the boundary.

    shapefiles = [
        entry.path
        for entry in os.scandir(extracted_location)
        if entry.is_file() and entry.name.endswith(('.shp', '.SHP'))
    ]

    name = os.path.basename(extracted_location)

    if not shapefiles:
        raise ValueError(
            f'Unable to find corresponding shapefile in {extracted_location}'
        )

    if len(shapefiles) > 1:
        raise NotImplementedError(
            f'Found more than one shapefile in {extracted_location}. '
            'This is unexpected.'
        )

    os.makedirs(generated_location, exist_ok=True)
    destination = os.path.join(generated_location, name + '_geojson.json')

    # This is using fiona behinds the scenes which is what I wanted to use
    # in the first place, but its own API is not as clear how to achieve this.
    gdf = geopandas.read_file(shapefiles[0])
    gdf.to_file(destination, driver='GeoJSON')


def download_extract_all(download_directory, extracted_location):
    # It would be better if this was asynchronous and could download at least
    # two things at once.
    for uri in DATA_2021.values():
        downloaded_data = download(uri, download_directory)
        if not downloaded_data.endswith(('.zip', '.ZIP')):
            raise ValueError('Expect ZIP files only, at this time.')

        extracted_data = extract(downloaded_data, extracted_location)

        # yield uri, downloaded_data, extracted_data


if __name__ == '__main__':
    # The default action is to to do its only action.

    # The default locations are specific to the script author as it makes
    # development easier. The idea would be use ini file to define this instead
    # and instead default to Data/Download, Data/Extracted, Data/Generated.
    parser = argparse.ArgumentParser(
        description='Download and extract ABS boundaries. By default it will '
        'convert the state boundaries to GeoJSON (subject to change).'
    )
    parser.add_argument(
        '--download-location',
        help='The location where the source data will be downloaded.',
        default=f'G:\GeoData\Source\ABS - Australia',
    )
    parser.add_argument(
        '--extracted-location',
        help='The location where the source data will be extracted.',
        default=f'G:\GeoData\Extracted\ABS\ASGS_Boundaries',
    )
    parser.add_argument(
        '--generated-location',
        help='The location where the generated/derived data will be stored.',
        default=f'G:\GeoData\Generated\ASGS_Boundaries',
    )
    arguments = parser.parse_args()

    states_download = download(
        DATA_2021[abs.GeographicStructures.STE], arguments.download_location
    )
    states_extracted = extract(states_download, arguments.extracted_location)
    convert_boundary_to_geojson(states_extracted, arguments.generated_location)
