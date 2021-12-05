"""Operates on data from AEMO. The first step was to read the source data and
construct a single file for further analysis. That single file was intended to
be an Apache Parquet but I have wasted a couple of hours trying to make that
work (the datetime field made it very difficult).

Definition files: https://visualisations.aemo.com.au/aemo/nemweb/index.html

Source: https://www.nemweb.com.au/Reports/Archive/Dispatch_SCADA/

# https://nemweb.com.au/Reports/ARCHIVE/ROOFTOP_PV/ACTUAL/

# https://www.nemweb.com.au/Reports/Archive/ROOFTOP_PV/ACTUAL/
# PUBLIC_ROOFTOP_PV_ACTUAL_MEASUREMENT_20211118.zip


For historical data greater than 13 months there is:
https://nemweb.com.au/Data_Archive/Wholesale_Electricity/

The PV files are PUBLIC_DVD_ROOFTOP_PV_ACTUAL.

Started 2021-04-05.
Major update: 2021-12-04 - Solar data parquet.

Known limitations:
- bulk_convert_to_parquet() - does not support files with more than one report
  sub-type in them.
"""

import csv
import datetime
import io
import os
import zipfile

import pandas
import pyarrow
import pyarrow.parquet
import yaml


__version__ = '0.1.0'
__copyright__ = "Copyright 2021, https://github.com/donno/"


def rows_to_data_frame(rows):
    """Return a data frame based on the data from the rows."""

    names = None
    data = []

    for row in rows:
        if not names and row[0] == 'I':
            names = row[4:]
        elif row[0] == 'D':
            # row[1] is the report type.
            # row[2] is the report sub-type.
            # row[3] is the report version.
            #
            # For rooftop-pv-actual they are 'ROOFTOP', 'ACTUAL' and 2
            # respectively.
            data.append(row[4:])

    return pandas.DataFrame(data, columns=names)


def parquet_schema(definition_filename, extended_fields=True):
    """Parse the definition from a YAML file into a Arrow/Parquet schema.

    The schema of the Apache Parquet file will be based on the given definition
    provided in YAML in definition_path. This definition file comes from:
    https://visualisations.aemo.com.au/aemo/nemweb/index.html

    Parameters
    ----------
    definition_filename : str or pathlib.Path
        The path to the YAML definition file used to define the schema.
    extended_fields : bool, default True
        Include additional metadat about the fields (their description).

    Returns
    -------
    schema : pyarrow.Schema
    """

    class Loader(yaml.SafeLoader):
        @staticmethod
        def field_constructor(loader, tag_suffix_or_node, node=None):
            if not node:
                node = tag_suffix_or_node
                tag_suffix = None
            else:
                tag_suffix = tag_suffix_or_node

            raise NotImplementedError('Harder than it looks')

    Loader.add_constructor(
        u'!file',
        yaml.constructor.SafeConstructor.construct_yaml_map)
    Loader.add_constructor(
        u'!report',
        yaml.constructor.SafeConstructor.construct_yaml_map)
    Loader.add_constructor(
        u'!field',
        yaml.constructor.SafeConstructor.construct_yaml_map)

    with open(definition_filename, 'r') as reader:
        definition = yaml.load(reader, Loader)

    # Anything else is not expected and might mean multiple schemas are needed.
    assert len(definition['reports']) == 1

    def format_to_type(format: str):
        if format == 'DATE':
            return pyarrow.date64()
        elif format.startswith('VARCHAR2'):
            return pyarrow.string()
        elif format.startswith('NUMBER('):
            # NUMBER(precision, scale)
            # precision - number of digits (including after decimal mark).
            # scale - number to the right.
            #
            # TODO: consider switching between 32-bit float or 64-bit float.
            return pyarrow.float64()

        raise NotImplementedError(f'Unhandled format {format}')

    def convert_field_simple(field):
        return (field['name'], format_to_type(field['format']))

    def convert_field_detailed(field):
        return pyarrow.field(
            field['name'], format_to_type(field['format']),
            metadata={'description': field['description']}
        )

    convert_field = \
        convert_field_detailed if extended_fields else convert_field_simple

    return pyarrow.schema([
        convert_field(field)
        for field in definition['reports'][0]['fields']
    ],
        metadata={
        'name': definition['name'],
        'code': definition['reports'][0]['name'],
        'dataset': definition['dataset'],
        'description': definition['description'],
    },
    )


def bulk_convert_to_parquet(source_directory,
                            output_directory,
                            definition_path):
    """Convert CSV in source directory (including within ZIP files, ZIPs in
    ZIP files to a single Apache Parquet file in output_directory.

    The schema of the Apache Parquet file will be based on the given definition
    provided in YAML in definition_path. This definition file comes from:
    https://visualisations.aemo.com.au/aemo/nemweb/index.html

    Parameters
    ----------
    source_directory : str or pathlib.Path
        The path to the directory containing the files to convert.
    output_directory : str or pathlib.Path
        The path to the directory where the output file should be written.
    definition_path : str or pathlib.Path
        The path to the YAML definition file used to define the schema of the
        source and output files.
    """

    # Determine source files.
    def _source_file_paths(source_directory):
        for entry in os.scandir(source_directory):
            if entry.is_file() and entry.name.endswith('.zip'):
                if not zipfile.is_zipfile(entry.path):
                    raise ValueError(
                        f'Expected "{entry.path}" to be a zip file')
                yield entry.path
            else:
                print(f'Unhandled file: {entry.name}')

    frames = []

    def _handle_rows(rows):
        # The first record in the rows is a code and is one of D, C and I.
        frame = rows_to_data_frame(rows)

        if sorted(schema.names) != sorted(frame.columns):
            # TODO: Create diff of the sets.
            raise TypeError('Data does not match schema.')

        # Convert columns to the correct type.
        DATE_FORMAT = '%Y/%m/%d %H:%M:%S'
        for name, type_ in zip(schema.names, schema.types):
            if type_ == pyarrow.float64():
                frame[name] = pandas.to_numeric(frame[name])
            elif type_ == pyarrow.date64():
                frame[name] = pandas.to_datetime(frame[name],
                                                 format=DATE_FORMAT)

        frames.append(frame)

    schema = parquet_schema(definition_path)
    dataset = schema.metadata[b'dataset'].decode('utf-8')

    # TODO: This could be used to match the filename to the YAML files.
    # dataset_to_name_prefix = {
    #     'rooftop-pv-actual': 'PUBLIC_ROOFTOP_PV_ACTUAL_MEASUREMENT_',
    # }

    for path in _source_file_paths(source_directory):
        process_zip(path, _handle_rows)

    frame = pandas.concat(frames)
    arrays = [frame[name].to_numpy() for name in schema.names]

    frame.to_parquet(os.path.join(output_directory,
                                  dataset + '.pandas.parquet'))

    writer = pyarrow.parquet.ParquetWriter(
        os.path.join(output_directory, dataset + '.parquet'),
        schema)
    writer.write_table(pyarrow.table(arrays, schema=schema))
    writer.close()


def rooftop_pv_actual(records):
    """Processes rooftop photovoltaic actuals.

    Estimate of regional Rooftop Solar actual generation for each half-hour
    interval in a day

    Source: https://nemweb.com.au/Reports/Current/ROOFTOP_PV/ACTUAL/
    Filename prefix: PUBLIC_ROOFTOP_PV_ACTUAL_MEASUREMENT_

    Example:
    I,ROOFTOP,ACTUAL,2,INTERVAL_DATETIME,REGIONID,POWER,QI,TYPE,LASTCHANGED
    D,ROOFTOP,ACTUAL,2,"2021/11/20 22:30:00",NSW1,0,1,MEASUREMENT,"2021/11/20 22:49:35"
    """

    # See rooftop-pv-actual-definition.yaml for further details.

    # First column has a code:
    # C = Comment
    # D = Data
    # I -> Info?

    # C,NEMP.WORLD,ROOFTOP_PV_ACTUAL_MEASUREMENT,AEMO,PUBLIC,
    # 2021/12/04,23:00:17,0000000353766302,DEMAND,0000000353766302
    for record in records:
        if record[0] == 'D':
            assert record[1] == 'ROOFTOP'
            assert record[2] == 'ACTUAL'

            # The info line wo uld verify this.
            interval = record[3]

            # Region identifier - 20 characters.
            region = record[4]
            power = record[5]
            quality_indicator = record[6]

            # Entry type is one of DAILY, MEASUREMENT or SATELLITE.
            entry_type = record[7]

            last_changed = record[8]

            # print(record)


def process_csv_from_zip(zip_reader, name, handler):
    print(f'Reading {name} from {os.path.basename(zip_reader.filename)}')

    with zip_reader.open(name, 'r') as csv_contents:
        csv_reader = csv.reader(io.TextIOWrapper(csv_contents))
        handler(csv_reader)


def process_zip(path, handler=None):
    def _handler(records):
        for record in records:
            print(record)

    # Set a default handle if none is provided.
    handler = handler or _handler

    if not zipfile.is_zipfile(path):
        raise TypeError('Expected path to be a zip file')

    with zipfile.ZipFile(path, 'r') as reader:
        for item in reader.infolist():
            if item.filename.endswith(('.csv', '.CSV')):
                csv_name = item.filename
                process_csv_from_zip(reader, csv_name, handler)
            elif item.filename.endswith('.zip'):
                with zipfile.ZipFile(reader.open(item)) as inner_reader:
                    if len(inner_reader.namelist()) != 1:
                        raise ValueError('Expected only a single CSV.')

                    csv_name = inner_reader.namelist()[0]
                    process_csv_from_zip(inner_reader, csv_name, handler)
            else:
                raise TypeError('Expected ZIP to only contain zips')


def plot_pv():
    """The first plot is each region as a line series over time.

    The second plot divided into 4 plots for each season.
    """
    import matplotlib.dates as plotdates
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(1)
    frame = pandas.read_parquet('data/rooftop-pv-actual.pandas.parquet')
    for region, data in frame.groupby('REGIONID'):
        axis.plot(data['INTERVAL_DATETIME'], data['POWER'], label=region)
    axis.set_ylim(bottom=0)
    plt.xlabel('The forecast half-hour interval')
    plt.ylabel('Estimated generation in MW at the interval end (MW)')
    plt.title('Estimate of regional Rooftop Solar actual generation for each '
              'half-hour interval in a day')
    plt.legend()
    plt.show()
    plt.close()

    # Add additional columns (one for the season and one for time of day).
    frame['Season'] = (frame['INTERVAL_DATETIME'].dt.month % 12) // 3

    # matlibplot can't plot times, it must be datetimes.
    today = datetime.date.today()
    frame['Time'] = [
        datetime.datetime.combine(today, time)
        for time in frame['INTERVAL_DATETIME'].dt.time
    ]

    fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)
    time_formatter = plotdates.DateFormatter('%H:%M')

    # Set-up the titles.
    fig.suptitle(
        'Estimate of regional Rooftop Solar actual generation for each '
        'half-hour interval in a day by season\nFor South Australia.')
    axs[0, 0].set_title("Summer")
    axs[0, 0].xaxis.set_major_formatter(time_formatter)
    axs[0, 1].set_title("Autumn")
    axs[0, 1].xaxis.set_major_formatter(time_formatter)
    axs[1, 0].set_title("Winter")
    axs[1, 0].xaxis.set_major_formatter(time_formatter)
    axs[1, 1].set_title("Spring")
    axs[1, 1].xaxis.set_major_formatter(time_formatter)

    # Consider writing out a separate figure per-region, if not
    # it really needs to be the average for each region or average, 95th,
    # and 5th percentiles.
    for season, data in frame.groupby('Season'):
        for region, region_data in data.groupby('REGIONID'):
            if region.startswith('SA'):
                axs.ravel()[season].plot(region_data['Time'],
                                        region_data['POWER'],
                                        label=region)

    for axis in axs.ravel():
        axis.set_ylim(bottom=0)

    plt.tight_layout()
    plt.legend()
    plt.show()


if __name__ == '__main__':
    #source_data = os.path.join('data', 'PUBLIC_DISPATCHSCADA_20200306.zip')
    # process_zip(source_data)

    # bulk_convert_to_parquet(
    #     'G:/GeoData/Source/NEMWEB/ARCHIVE/ROOFTOP_PV_ACTUAL', 'data',
    #     'rooftop-pv-actual-definition.yaml')

    plot_pv()
