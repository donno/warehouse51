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
                        This can be the unique ID for the locality or its name.
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

    street_locality = pandas.read_csv(street_locality_file,
                                      sep='|',
                                      usecols=street_locality_columns)
    address_detail = pandas.read_csv(address_detail_file,
                                    sep='|',
                                     dtype={
                                         'BUILDING_NAME': str,
                                         'NUMBER_FIRST': str,
                                         'NUMBER_FIRST_SUFFIX': str,
                                     },
                                     keep_default_na=False,
                                     usecols=should_keep_address_detail_column)
    address_geocode = pandas.read_csv(address_default_geocode_file,
                                      sep='|',
                                      usecols=geocode_columns)

    if filter_to_locality:
        # Filter address detail down to a specific locality
        if not filter_to_locality.startswith('loc'):
            # The locality was not the ID, so assume it is the name.
            filter_to_locality = find_locality_by_name(base_directory,
                                                       filter_to_locality)

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


def with_mesh_block(base_directory, address_view):
    """Return the address view with the mesh block data included.

    A mesh block is the smallest geographic areas defined by the Australian
    Bureau of Statistics (ABS) and forms larger building block.

    This is currently limited to South Australia.
    The data files are separated based on states and territories.

    base_directory: The directory that contains the G-NAF data.
                    It should contain 'Standard' and 'Authority Code' folders.)
    """
    address_mesh_block_file = os.path.join(
        base_directory, 'Standard', 'SA_ADDRESS_MESH_BLOCK_2021_psv.psv')

    mesh_block_columns = [
        "ADDRESS_DETAIL_PID", "MB_2021_PID",
    ]

    mesh_block_files = pandas.read_csv(address_mesh_block_file,
                                       sep='|',
                                       usecols=mesh_block_columns)

    return address_view.join(
        mesh_block_files.set_index('ADDRESS_DETAIL_PID'),
        on='ADDRESS_DETAIL_PID')


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


def add_full_address_with_locality(base_directory, address_view,
                                   use_short_street_type=True):
    """Adds the name of the locality (essentially suburb).

    This requires the base directory for the data as it needs to load an
    additional data file.

    This doesn't require add_full_address() to be called first.
    """

    #address_view['FULL_ADDRESS'] = address_view.apply(_address, axis=1)
    locality_file = os.path.join(
        base_directory, 'Standard', 'SA_LOCALITY_psv.psv')
    locality = pandas.read_csv(locality_file, '|',
                               usecols=['LOCALITY_PID', 'LOCALITY_NAME'])

    # STREET_TYPE_CODE will be STREET, ROAD, COURT instead of ST, RD, CT.
    # For the purpose of this function lets use
    # the latter is needed instead the information can be looked up in
    # Authority_Code_STREET_TYPE_AUT_psv.psv to do the mapping.
    if use_short_street_type:
        street_type_aut_file = os.path.join(
            base_directory, 'Authority Code',
            'Authority_Code_STREET_TYPE_AUT_psv.psv')

        code_to_name = {}  # This is what it called in the file.
        with open(street_type_aut_file) as reader:
            next(reader)  # Skip the heading.
            for line in reader:
                code, name, _ = line.split('|')  # Description is the third.
                code_to_name[code] = name
    else:
        code_to_name = {}

    # Add the locality name column.
    address_view = address_view.join(
        locality.set_index('LOCALITY_PID'),
        on='LOCALITY_PID',
    )

    def _create_full_address(row):
        address = _address(row)
        if use_short_street_type:
            # This feature would be simpler if it was part of the  _address
            # function.
            street_type_code = address.split(' ')[-1]
            name = code_to_name[street_type_code]
            address = address[:-len(street_type_code)] + name

        return '{} {}'.format(address, row['LOCALITY_NAME'])

    address_view['FULL_ADDRESS'] = address_view.apply(_create_full_address,
                                                      axis=1)
    return address_view


def print_addresses(address_view):
    transform = latlong_to_cartesian()

    if 'FULL_ADDRESS' in address_view:
        for _, item in address_view.iterrows():
            lat, lng = transform(item['LATITUDE'], item['LONGITUDE'])
            print('%.14f,%.14f,%s' % (lat, lng, item['FULL_ADDRESS']))
    else:
        for _, item in address_view.iterrows():
            lat, lng = item['LATITUDE'], item['LONGITUDE']
            print('%.14f %.14f %s' % (lat, lng, _address(item)))


def latlong_to_cartesian():
    """Return a callable that can be given the latitude/longitude which in
    turn will return the Cartesian coordinates."""
    source = pyproj.CRS.from_epsg(4326)  # WGS84
    destination = pyproj.CRS.from_epsg(8059)  # GDA2020 / SA Lambert
    return pyproj.Transformer.from_crs(source, destination).transform


def find_locality_by_name(base_directory, name):
    # Either add: exact=True or False or glob.

    # This function is not efficient if you need to look-up multiple IDs from
    # names.
    locality_file = os.path.join(
        base_directory, 'Standard', 'SA_LOCALITY_psv.psv')

    locality = pandas.read_csv(locality_file,
                               sep='|',
                               usecols=['LOCALITY_PID', 'LOCALITY_NAME'])

    mask = locality['LOCALITY_NAME'] == name.upper()
    if mask.any():
        result = locality['LOCALITY_PID'].loc[mask]
        return result.item()
    else:
        raise ValueError(f'No locality with "{name}" found.')


if __name__ == '__main__':
    base_directory = r'G:\GeoData\Extracted\G-NAF\G-NAF AUGUST 2023'

    # The structure of the locality_pid changed between the May 2021 and the
    # August 2021 releases of the G-NAF data set, so it starts with loc and
    # then as 12 alphanumeric characters.  The August 2021 release was meant
    # to contain a mapping.
    #
    # SA2 / loc88df4c1f6c87 is Adelaide the capital city of South Australia.
    # SA608 / locef2ffb75f36f is an old mining town in regional South Australia.
    view = pandas_address_view(base_directory,
                               filter_to_locality='Iron Knob')
    add_full_address(view)
    print_addresses(view)
