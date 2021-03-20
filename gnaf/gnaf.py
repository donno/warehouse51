"""GNAF is the Geocoded National Address File.

The G-NAF is Australia's authoritative, geocoded address file.
It is produced by PSMA Australia (psma.com.au) but is freely
available.

The data for this script is available from:
  https://data.gov.au/dataset/geocoded-national-address-file-g-naf

Detail of the file format:
  http://gnafld.net/def/gnaf
"""

import os

import pandas

import pyproj


def pandas_address_view(base_directory, filter_to_locality=None):
    """Read in the G-NAF for South Australia and provides a view onto the data.

    This is currently limited to South Australia.
    The data files are separated based on states and territories.

    base_directory: The directory that contains the G-NAF data.
                    It should contain 'Standard' and 'Authority Code' folders.

    filter_to_locality: This enables filtering down to a particular locality
                        which may be a city or a suburb.
    """

    # Define the paths required
    street_locality_file = os.path.join(
        base_directory, 'Standard', 'SA_STREET_LOCALITY_psv.psv')
    address_detail_file = os.path.join(
        base_directory, 'Standard', 'SA_ADDRESS_DETAIL_psv.psv')
    address_default_geocode_file = os.path.join(
        base_directory, 'Standard', 'SA_ADDRESS_DEFAULT_GEOCODE_psv.psv')

    # Load the data
    #
    # Only keep these columns as things like the creation date aren't needed.
    street_locality_columns = [
        "STREET_LOCALITY_PID", "STREET_CLASS_CODE", "STREET_NAME",
        'STREET_TYPE_CODE', 'STREET_SUFFIX_CODE',
    ]

    address_detail_columns_to_ignore = {
        'DATE_CREATED', 'DATE_LAST_MODIFIED', 'DATE_RETIRED', 'GNAF_PROPERTY_PID',
    }

    geocode_columns = [
        'ADDRESS_DETAIL_PID', 'LONGITUDE', 'LATITUDE',
        # GEOCODE_TYPE_CODE helps identifier where it refers to.
    ]

    def should_keep_address_detail_column(column):
        return column not in address_detail_columns_to_ignore

    street_locality = pandas.read_csv(street_locality_file, '|',
                                      usecols=street_locality_columns)
    address_detail = pandas.read_csv(address_detail_file, '|',
                                     dtype={
                                         'BUILDING_NAME': str,
                                         'NUMBER_FIRST': str,
                                         'NUMBER_FIRST_SUFFIX': str,
                                     },
                                     keep_default_na=False,
                                     usecols=should_keep_address_detail_column)
    address_geocode = pandas.read_csv(address_default_geocode_file, '|',
                                      usecols=geocode_columns)

    if filter_to_locality:
        # Filter address detail down to a specific locality
        address_detail = address_detail.loc[
            address_detail['LOCALITY_PID'] == filter_to_locality]

    merged = address_detail.join(
        street_locality.set_index('STREET_LOCALITY_PID'),
        on='STREET_LOCALITY_PID',
        lsuffix='_address', rsuffix='_street')

    merged = merged.join(
        address_geocode.set_index('ADDRESS_DETAIL_PID'),
        on='ADDRESS_DETAIL_PID',
        rsuffix='_geocode')

    return merged


def _address(row):
    flat_prefix = row['FLAT_NUMBER'] + '/' if row['FLAT_NUMBER'] else ''
    if row['FLAT_NUMBER'] and row['FLAT_TYPE_CODE'] == 'SHOP':
        flat_prefix = 'SHOP ' + flat_prefix

    if row['NUMBER_FIRST']:
        number = flat_prefix + row['NUMBER_FIRST'] + row['NUMBER_FIRST_SUFFIX']
        if row['NUMBER_LAST']:
            number += '-' + row['NUMBER_LAST'] + row['NUMBER_LAST_SUFFIX']
    else:
        assert not row['NUMBER_FIRST_SUFFIX']
        number = 'LOT ' + flat_prefix + row['LOT_NUMBER']

    return '{} {} {}'.format(
        number, row['STREET_NAME'], row['STREET_TYPE_CODE'])


def add_full_address(address_view):
    address_view['FULL_ADDRESS'] = address_view.apply(_address, axis=1)
    return address_view


def print_addresses(address_view):
    transform = latlong_to_cartsian()

    if 'FULL_ADDRESS' in address_view:
        for _, item in address_view.iterrows():
            lat, lng = transform(item['LATITUDE'], item['LONGITUDE'])
            print('%.14f,%.14f,%s' % (lat, lng, item['FULL_ADDRESS']))
    else:
        for _, item in address_view.iterrows():
            lat, lng = item['LATITUDE'], item['LONGITUDE']
            print('%.14f %.14f %s' % (lat, lng, _address(item)))


def latlong_to_cartsian():
    """Return a callable that can be given the latitude/longitude which in
    turn will return the Cartesian coordinates."""
    source = pyproj.CRS.from_epsg(4326)  # WGS84
    destination = pyproj.CRS.from_epsg(8059)  # GDA2020 / SA Lambert
    return pyproj.Transformer.from_crs(source, destination).transform


if __name__ == '__main__':
    base_directory = r'G:\GeoData\Extracted\G-NAF\G-NAF FEBRUARY 2020'

    # SA608 is an old mining town in regional South Australia.
    view = pandas_address_view(base_directory, filter_to_locality='SA608')
    add_full_address(view)
    print_addresses(view)
