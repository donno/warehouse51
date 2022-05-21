"""Convert Geocoded National Address File (G-NAF) into database suitable for
Datasette.

This is an early work-in progress and I haven't gotten it into a state where it
is nice to use with Datasette.

The G-NAF is Australia's authoritative, geocoded address file.
It is produced by PSMA Australia (psma.com.au) but is freely available.

The data for this script is available from:
  https://data.gov.au/dataset/geocoded-national-address-file-g-naf

Detail of the file format:
  http://gnafld.net/def/gnaf

Features:
- Single database for entire nation
  The "State" table would be merged.
- Database for each state.
"""

import os
import itertools
import pandas
import pandas.io.sql
import numpy

from sqlalchemy import create_engine

SINGLE_DATABASE = False

STATES = {'WA', 'VIC', 'SA'}
TERRITORIES = {'ACT', 'NT'}

def all_files(path):
    for entry in os.scandir(os.path.join(path, 'Standard')):
        if entry.name.endswith(('.psv', '.csv')):
            yield entry.path

def files_by_state_or_territory(path):
    files = list(all_files(path))

    def prefix(path: str):
        return os.path.basename(path).partition('_')[0]

    return itertools.groupby(files, key=prefix)


def create_sql_table(connection, frame, table_name, keys=None, dtype=None):
    """Create SQL table from the given frame."""

    # This function without any changes would be same a
    # pandas.io.sql.get_schema()

    # This uses parts in pandas for the heavy lifting but enables creating
    # foreign keys.
    database = pandas.io.sql.SQLDatabase(connection, schema=None, meta=None)
    table = pandas.io.sql.SQLiteTable(
        table_name, database,
        frame=frame, index=False, keys=keys, dtype=dtype,
    )
    table.if_exists = 'replace'
    table.create()  # This is where it could be customised.

    # High level: sql_for_table = str(table.sql_schema())
    sql_for_table = str(";\n".join(table.table))
    return sql_for_table


def import_state(files):
    files = list(files)

    name_only = [
        os.path.splitext(os.path.basename(path))[0].replace('_psv', '')
        for path in files
    ]

    state = os.path.basename(name_only[0]).partition('_')[0]
    engine = create_engine(f'sqlite:///gnaf_{state.lower()}.db')
    sqlite_connection = engine.connect()

    for name, path in zip(name_only, files):
        state, _, table_name = os.path.basename(name).partition('_')
        print(f'Importing {table_name}')
        table = pandas.read_csv(path, sep='|')


        table.to_sql(table_name, sqlite_connection, index=False,
                     if_exists='append')

    sqlite_connection.close()

if __name__ == '__main__':
    base_directory = r'G:\GeoData\Extracted\G-NAF\G-NAF FEBRUARY 2020'
    for state, files in files_by_state_or_territory(base_directory):
        print(state)
        print('----')
        import_state(files)
        break
