"""A module for working with the geometry such as election boundaries.

Data Licencing
--------------
Uses of the data downloaded by the script requires the end-users are aware the
the data was sourced from the Australian Electoral Commission and is used under
licence. The following copyright statement shall be used:
    © Commonwealth of Australia (Australian Electoral Commission)2023

The copyright statement can be preceded by the following when used in a
derivative product:
    This product (XXXX) incorporates data that is:
"""

import dataclasses
import pathlib
import types
import urllib.request

import shapefile  # pyshp on PyPi


# That licence for the data can be read here:
# https://www.aec.gov.au/Electorates/gis/licence.htm
ELECTORAL_BOUNDARY_NATIONAL = 'https://aec.gov.au/Electorates/gis/files/2021-Cwlth_electoral_boundaries_ESRI.zip'

URIS_BY_STATE_OR_TERRITORY = {
    'NT': 'https://www.aec.gov.au/Electorates/gis/files/NT-Feb_2017-ESRI.zip',
    'SA': 'https://www.aec.gov.au/Electorates/gis/files/sa-july-2018-esri.zip',
    'WA': 'https://www.aec.gov.au/Electorates/gis/files/wa-august-2021-esri.zip',
    'VIC': 'https://www.aec.gov.au/Electorates/gis/files/vic-july-2021-esri.zip',
    'ACT': 'https://www.aec.gov.au/Electorates/gis/files/act-july-2018-esri.zip',
    'NSW': 'https://www.aec.gov.au/Electorates/gis/files/nsw-esri-06042016.zip',
    'QLD': 'https://www.aec.gov.au/Electorates/gis/files/qld-march-2018-esri.zip',
    'TAS': 'https://www.aec.gov.au/Electorates/gis/files/tas-november-2017-esri.zip',
}


    # Field name: the name describing the data at this column index.
    # Field type: the type of data at this column index. Types can be:
    #     "C": Characters, text.
    #     "N": Numbers, with or without decimals.
    #     "F": Floats (same as "N").
    #     "L": Logical, for boolean True/False values.
    #     "D": Dates.
    #     "M": Memo, has no meaning within a GIS and is part of the xbase spec instead.
    # Field length: the length of the data found at this column index. Older GIS software may truncate this length to 8 or 11 characters for "Character" fields.
    # Decimal length: the number of decimal places found in "Number" fields.



@dataclasses.dataclass
class FieldDefinition:
    """Represent the definition of a field from an ERSI Shapefile."""

    name: str
    """The name description the data at this column index."""

    field_type: str
    """The type of data at this column index.

    Types can be C for Characters/text, N for numbers, F for floats, L for
    logical/booleans, D for dates and M for memo.
    """

    field_length: int
    """The length of the data found at this column index."""

    decimal_length: int
    """The number of decimal places found in the field if is a number."""


def download_if_missing(uri=ELECTORAL_BOUNDARY_NATIONAL) -> pathlib.Path:
    filename = pathlib.Path(uri).name
    expected_path = pathlib.Path(__file__).parent / "data" / filename
    if not expected_path.is_file():
        urllib.request.urlretrieve(uri, expected_path)
    return expected_path



# Provide different levels of access to the data.
# - Country (outline)
# - States (all)
# - State (single state)
# - Division (all)
# - Division (single state)
# - Division (single  division)
# TODO: Provide the above.
#
# The source file seems to lack information about which polygons are for what
# state, it is only the electrical divisions.

def dump(source: shapefile.Reader):
    """Dump data from source to standard output.

    This is intended as a development aid.
    """
    print("Fields")
    for field in source.fields[1:]:  # Ignore the definition flag.
        print(' ', FieldDefinition(*field))
    print()

    print('Records')
    # for shape in source.records():
    #     print(shape)


def rebuild(source: shapefile.Reader):
    """Rebuild the shapefile into a simplified sqlite database."""
    raise NotImplementedError("NYI - not sure this path should be taken.")


class Australia:
    """Represents the federal electoral boundary of Australia.
    """

    # Bonus would be including what year it is relevant for.

    def __init__(self, source):
        self.source = source
        print(self.source.fields)

        # Ignore the definition flag.
        self._field_names = [
            field[0] for field in self.source.fields[1:]
        ]

        # Example data:
        #  E_div_numb=15, Elect_div='Tangney', Numccds=411, Actual=117986,
        #  Projected=120085, Total_Popu=0, Australian=0, Area_SqKm=101.97,
        #  Sortname='Tangney')

    # TODO: Provide a function which provides just the outline of Australia.

    @property
    def divisions(self):
        """The federal electoral divisions."""
        for shape, record in zip(source.iterShapes(), source.iterRecords()):
            new_record = dict(zip(self._field_names, record))
            yield types.SimpleNamespace(**new_record), shape

if __name__ == '__main__':

    # Download all the shapefiles for the states and territories.
    for uri in URIS_BY_STATE_OR_TERRITORY.values():
        download_if_missing(uri)

    with shapefile.Reader(download_if_missing()) as source:
        dump(source)

        national = Australia(source)

        # Record contains the information such as name, size etc and population.
        for record, shape in national.divisions:
            print(record)
            print(shape)

        #print(shape.__geo_interface__['type'])

