"""Parse a DT1 file (Digital Terrain Elevation Data).

The file format was developed by National Geospatial-Intelligence Agency (GDA).
It was created as a standard for digital datasets, specially Digital Terrain
Elevation Data (DTED).

The specification can be found here:
  https://earth-info.nga.mil/publications/specs/printed/89020B/89020.pdf

Each terrain elevation data file consists of the User Header Label(UHL),
Data Set Identification(DSI) Record, AccuracyDescription Record(ACC) and
the Data records.

DTED Level 1 and 2
User header Label ( UTL: 80 bytes) start at byte 1
Data Set Identification  starts at byte

Level 1: Data Records - each record is about 2414 bytes
Level 2: Data Records - each record is about 7214 bytes

See http://everyspec.com/MIL-PRF/MIL-PRF-080000-99999/MIL-PRF-89020B_25316/
Also see https://www.dlr.de/eoc/en/Portaldata/60/Resources/dokumente/7_sat_miss/SRTM-XSAR-DEM-DTED-1.1.pdf
Important numbers:
- spacing of three arc seconds is approximately 100 metres.
- spacing of one arc second is approximately 30 meters.

Data Providers
- The Shuttle Radar Topography Mission (SRTM, DTS-99) from February 2000 was
  an US-German-Italian effort to produce a first global digital elevation model
  (DEM). The data associated with that mission is
https://www.europeandataportal.eu/data/datasets/f4d4079a-ada3-41d0-ba95-630ba232e147
"""

import csv
import io

security_code_mapping = {
    'S': 'Secret',
    'C': 'Confidential',
    'U': 'Unclassified',
    'R': 'Restricted',
}

def parse_user_header_label(reader):
    """Read the next portion as the User header label.

    This seems to be an artefact/feature of magnetic tapes.

    The length of the label is 80 bytes.
    """
    recognition_sentinel = reader.read(3)
    if recognition_sentinel != 'UHL':
        raise ValueError('Expected User header Label')

    if reader.read(1) != '1':
        raise ValueError('Expected 1 as required by the standard')

    class UserHeaderLabel:
        pass

    def parse_dddmmssh(dddmmssh):
        ddd = int(dddmmssh[:3], base=10)
        mm = int(dddmmssh[3:5], base=10)
        ss = int(dddmmssh[5:7], base=10)
        h = dddmmssh[-1]

        return ddd + mm / 60.0 + ss / 3600.0, h

    header = UserHeaderLabel()

    # 8 bytes, DDDMMSSH
    # Longitude of origin (lowerleft corner of data set;full degree value; leadingzero(s) for all subfields:degrees, minutes andseconds).  H is theHemisphere of the data.
    header.longitude_of_origin = parse_dddmmssh(reader.read(8))
    header.latitude_of_origin = parse_dddmmssh(reader.read(8))

    header.longitude_intervals = int(reader.read(4)) # tenths of seconds.
    header.latitude_intervals = int(reader.read(4)) # tenths of seconds.

    header.absolute_vertical_accuracy = reader.read(4) # in metres.

    header.security_code = security_code_mapping[reader.read(3).strip()]

    header.unique_reference = reader.read(12)

    header.longitude_line_count = int(reader.read(4))
    header.latitude_line_count = int(reader.read(4))

    header.multiple_accuracy = reader.read(1)
    # 0 for single, 1 for multiple.

    print(header.security_code)
    print(header.multiple_accuracy)

    reserved = reader.read(24)

    # myLongitudeOrigin = longitudeDegrees + longitudeMinutes/60.0 +
    #   longitudeSeconds/3600.0;

    header.longitude_line_spacing = header.longitude_intervals / 10.0 / 3600.0
    header.latitude_line_spacing = header.latitude_intervals / 10.0 / 3600.0

    return header

def parse_data_set_identification(reader):
    """


    Starts at byte 81
    Length is 648 bytes
    """

    # This expects reader to be at DSI which should be at byte 80.
    recognition_sentinel = reader.read(3)
    if recognition_sentinel != 'DSI':
        raise ValueError('Expected Data Set Identification record')

    security_code = security_code_mapping[reader.read(1).strip()]
    print(security_code)

    security_control_release_markings = reader.read(2)
    print(security_control_release_markings)
    security_handling_description = reader.read(27).strip()
    print(security_handling_description)

    reserved = reader.read(26)

    nima_series_designator = reader.read(5)
    if nima_series_designator != 'DTED1':
        raise ValueError('Expected DTED1')

    unique_reference = reader.read(15)

    reserved = reader.read(8)

    data_edition_number = reader.read(2)
    match_merge_version = reader.read(1)
    maintenance_date = reader.read(4)
    match_merge_date = reader.read(4)
    maintenance_description_code = reader.read(4)
    producer_code = reader.read(8) # CCAABB

    reserved = reader.read(16)

    product_specification = reader.read(9)
    if product_specification != 'PRF89020B':
        raise ValueError('Expected specification to be PRF89020B')

    product_specification_amendment = reader.read(1)
    product_specification_change = reader.read(1)

    product_specification_date = reader.read(4) # YYMM
    if product_specification_date != '0005':
        raise ValueError('Expected specification to be May 2000')

    print(unique_reference)
    print(product_specification, product_specification_date)

    vertical_datum = reader.read(3)
    print('vertical_datum', vertical_datum)
    horizontal_datum = reader.read(5)
    if horizontal_datum != 'WGS84':
        raise ValueError('Expected horizontal datum to be WGS84 as per PRF89020B')

    collection_system = reader.read(10)
    # SRTM = Shuttle Radar Topography Mission

    compilation_date = reader.read(4) # YYMM
    # TODO: parse this into a real date.

    print(collection_system + ' on ' + compilation_date)

    reserved = reader.read(22)

    latitude_of_origin = reader.read(9)
    longitude_of_origin = reader.read(10)
    latitude_of_SW_corner = reader.read(7)
    longitude_of_SW_corner = reader.read(8)
    latitude_of_NW_corner = reader.read(7)
    longitude_of_NW_corner = reader.read(8)
    latitude_of_NE_corner = reader.read(7)
    longitude_of_NE_corner = reader.read(8)
    latitude_of_SE_corner = reader.read(7)
    longitude_of_SE_corner = reader.read(8)

    clockwise_orientation_angle = reader.read(9) # "DDDMMSS.S. true north.

    longitude_line_count = reader.read(4)
    latitude_line_count = reader.read(4)

    latitude_line_count = reader.read(4)
    longitude_line_count = reader.read(4)
    partial_cell_indicator = reader.read(2)
    reserved_for_nima = reader.read(101)
    reserved_for_producing_nation = reader.read(100)
    reserved_for_comments = reader.read(156)

    return int(longitude_line_count), int(latitude_line_count)


def parse_accuracy_description(reader):
    """Parse information from the Accuracy Description (ACC) Record.

    This expects reader to already be at the ACC record.

    The record has a fixed length of 2700 ASCII characters.
    """
    accuracy_description_record = io.StringIO(reader.read(2700))
    recognition_sentinel = accuracy_description_record.read(3)
    if recognition_sentinel != 'ACC':
        raise ValueError('Expected Accuracy Description record')

def parse_data_record(reader, header):
    """Parse information from the Data Record Description Record.

    This expects reader to already be at the data record.

    The record has a fixed length of 7214 bytes*
    *Not really sure. the document is unclear.

    The first record should start at 3429.
    The second would be 5843.
    """

    recognition_sentinel = reader.read(1)
    # The recognition_sentinel is 252 in octal, ak.a 0252 so 170 or 0xAA
    if recognition_sentinel != b'\xAA':
        raise ValueError('Expected Data Record')

    data_block_count = int.from_bytes(reader.read(3), byteorder='big')
    longitude_count = int.from_bytes(reader.read(2), byteorder='big')
    latitude_count = int.from_bytes(reader.read(2), byteorder='big')

    # Reference: 3.10.9.1
    # The SRTM DTED Level 1 and Level 2 data cells may contain voids.
    # The void areas will contain null values (-32,767) in lieu of the terrain elevations. The Partial Cell Indicator in the DSI record willidentify the percentage of data coverage.
    null_value = -32767

    for longitude_index in range(0, header.longitude_line_count):
        for latitude_index in range(0, header.latitude_line_count):
            # Fixed Binary denotes signed magnitude, right-justified binary integers.
            elevation = int.from_bytes(reader.read(2), byteorder='big', signed=False) # big or little? not sure yet.
            if elevation & 0x8000:
                # Signed number.
                elevation &= 0x7FFF
                elevation = -elevation

            if elevation == null_value:
                continue

            longitude = header.longitude_of_origin[0] + longitude_index * header.longitude_line_spacing
            latitude = header.latitude_of_origin[0] + latitude_index * header.latitude_line_spacing
            yield longitude, latitude, elevation

    #   if (buffer[i] & 0x8000)
    #   {
    #     // The data is stored in sign and magnitude format, convert into
    #     // two's complement.
    #     buffer[i] &= 0x7FFF;
    #     buffer[i] = -buffer[i];
    #   }

# NOTE: We normally transform to UTM

    checksum = reader.read(4)
    # Algebraic addition of contents of block.  Sum is computed as an integer
    # summation of 8-bit values (Fixed Binary).


def parse(path):

    # 80, 648, 2700 are the common sizes for the first threerecords.
    # data records vary. They are 2414 for level 1, 7214 for level 2.

    with open('dted_points.csv', 'w', newline='') as writer:
        csv_writer = csv.writer(writer, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        with open(path, 'rb') as reader:
            #text_reader = io.TextIOWrapper(reader, encoding="ascii")
            description = io.StringIO(reader.read(80).decode('ascii'))
            header = parse_user_header_label(description)
            description = io.StringIO(reader.read(648).decode('ascii'))
            parse_data_set_identification(description)

            description = io.StringIO(reader.read(2700).decode('ascii'))
            parse_accuracy_description(description)

            # The number of records is a function of the DTED level and latitude
            # 1201 for level 1
            # 3601 for level 2
            # 'cells between latitudue 50 degrees South and 50 degrees north.
            # Elevations are 2-byte integers, higher order, negatives as signed
            # magnitude.

            # while True:
            #     record = io.BytesIO(reader.read(2414))
            #     if not record:
            #         break
            #     h = record.read(1)
            #     print(h)
            #     if not h:
            #         break
            record = io.BytesIO(reader.read(2414))

            for record in parse_data_record(reader, header):
                csv_writer.writerow(record)

parse('e112_s26.dt1')
