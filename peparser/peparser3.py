"""Parse the Microsoft Portable Executable and Common Object File Format.

The use of the Construct library (http://construct.readthedocs.org/) is used to
facility defining the structures used in the file format which can then be
used to parse an executable.

The specification for the format can be found here:
    https://msdn.microsoft.com/en-us/windows/hardware/gg463119.aspx
This will be referred to as the specification document here.

The latest version is found at:
    https://learn.microsoft.com/en-us/windows/win32/debug/pe-format

The version of this script I wrote for Python 2, I had developed myself from
the documentation. It was only a week later that I found that there was an
example of the format in the library. For the Python 3 version, I've switched
to using the pe32coff module from the construct's gallery.

LICENSE      : The MIT License (see LICENSE.txt for details)

TODO         :
  - Parse the rest of the format, at the moment it only does the parts that I
    was interested in at the time.
  - Take more advantage of Construct such that its possible to do pe.parse(data)
    and it can resolve all the structures etc.
  - Add handling for the import table (the Python 2 / construct 2.5.3 handled
    that).
  - Revisit the RVA to file offset work. See if its possible to use
    section.rawdata instead of the entire file's data.

KNOWN ISSUES:
- Essentially imports(...) and output_bitmaps(...) have only been  tested with
  ski32.exe.

Notes:
- .didat -> delay load section

"""

import enum
import os
import pe32coff
from construct import *

class ResourceID(enum.IntFlag):
  CURSOR = 1
  BITMAP = 2
  ICON = 3
  MENU = 4
  DIALOG_BOX = 5
  STRING_TABLE_ENTRY = 6
  FONT_DIRECTORY = 7
  FONT = 8
  ACCELERATOR_TABLE = 9
  RAW_DATA = 10
  MESSAGE_TABLE_ENTRY = 11
  GROUP_CURSOR = 12
  GROUP_ICON = 14
  VERSION_INFORMATION = 16
  DLG_INCLUDE = 17
  PLUG_AND_PLAY = 19
  VXD = 20
  ANIMATED_CURSOR = 21
  ANIMATED_ICON = 22
  HTML = 23
  ASSEMBLY_MANIFEST = 24

resource_id_entry = Struct(
    "id" / Enum(Int32ul, ResourceID),  # Sometimes this is not an enum.
    "offset" / Int32ul,
)

resource_directory_table = Struct(
    "characteristics" / Int32ul,
    "datetime_stamp" / Int32ul,
    "major_version" / Int16ul,
    "minor_version" / Int16ul,
    "name_entry_count" / Int16ul,
    "id_entry_count" / Int16ul,
    "id_entries" / Array(this.id_entry_count, resource_id_entry)
)

resource_data_entry = Struct(
    "offset" / Int32ul,
    "size" / Int32ul,
    "code_page" / Int32ul,
    "reserved" / Int32ul,
)

# Begin structures for parsing the .idata section (also known as the import
# tables).
import_directory_entry = Struct(
    "import_name_table_address" / Int32ul,
    "time_date_stamp" / Int32ul,
    "forwarder_chain" / Int32ul,
    "name_address" / Int32ul,
    "import_address_table_address" / Int32ul,
  )

# Disclaimer: The 'seek' appears in the result.
import_directory_entries = Seek(this._.start_address) >> RepeatUntil(
    lambda obj, lst, ctx: obj.import_name_table_address == 0 and \
        obj.time_date_stamp == 0 and obj.forwarder_chain == 0 and \
        obj.name_address == 0 and obj.import_address_table_address == 0,
    import_directory_entry)

# An import lookup table is an array of 32-bit numbers for PE32 or an array of
# 64-bit numbers for PE32+.
#
# This field is really a bit field.
#  Ordinal vs Name flag
#  Ordinal Number
#  Hint/Name RVA (relative virtual address).
import_lookup_table = RepeatUntil(lambda obj, lst, ctx: obj == 0,
                                  pe32coff.plusfield)

# import_lookup_table = RepeatUntil(lambda obj, lst, ctx: obj == 0,
#     Construct(
#         "value" / pe32coff.plusfield
#         "is_symboltableindex" / Computed(this._linenumber == 0),
#     )
# )

hint_name_table_entry = Struct(
    "hint" / Int16ul,
    "name" / CString("ascii"),
  )


def parse(filename):
    with open(filename, 'rb') as reader:
        parsed_file = pe32coff.pe32file.parse_stream(reader)

    def find_data_directory(parsed_file, name):
        return next(
            directory
            for directory in parsed_file.optionalheader.datadirectories
            if directory.name == name
        )

    # Find the resource table.
    resource_directory = find_data_directory(parsed_file, 'resource_table')
    section = next(
        section for section in parsed_file.sections
        if section.virtual_address == resource_directory.virtualaddress)
    resource_table = resource_directory_table.parse(section.rawdata)

    return parsed_file, {
        'resource_table': resource_table,
        'resource_section': section,
    }


def output_bitmaps(raw_data, resources, output_directory):
    """Find bitmaps in an executable file and and extract them.

    The output_directory is created if it it doesn't exist.

    The resource table and section must be found already at this point. The
    parse() function handles that.
    """
    os.makedirs(output_directory, exist_ok=True)

    resource_table = resources['resource_table']
    resource_section = resources['resource_section']  # Yes same.
    print(resource_table)
    print(resource_section)
    bitmap_entry = next(entry for entry in resource_table.id_entries
                        if entry.id == 'BITMAP')

    # Find the resource_directory_table for the bitmaps.
    #
    # This is wrong, it slo where the 'enum' map is sometimes optional.
    bitmap_table_entry_address = bitmap_entry.offset ^ (1 << 31)
    bitmap_table = resource_directory_table.parse(
        resource_section.rawdata[bitmap_table_entry_address:])

    bitmap_header = bytearray([
        0x42, 0x4D, 0x76, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x76,
        0x00, 0x00, 0x00])

    for offset in (entry.offset for entry in bitmap_table.id_entries):
        sub_entry_table = resource_directory_table.parse(
            resource_section.rawdata[offset ^ (1 << 31):])

        for sub_entry in sub_entry_table.id_entries:
            entry = resource_data_entry.parse(
                resource_section.rawdata[sub_entry.offset:])

            entry_data = raw_data[entry.offset: entry.offset + entry.size]

            with open(os.path.join(output_directory,
                                  'file_%04x.bmp' % entry.offset),
                      'wb') as writer:
                writer.write(bitmap_header)
                writer.write(entry_data)


def imports(parsed_file, raw_data, verbose=True):
    """Print out information about the imports."""

    # This could potentially be refactored to be a generator similar to
    # groupby() where you first iterate over the libraries (import entries)
    # and then by the functions.

    import_table = next(
        directory
        for directory in parsed_file.optionalheader.datadirectories
        if directory.name == 'import_table')

    try:
        import_section = next(
            section for section in parsed_file.sections
            if section.name == '.idata')
    except StopIteration:
        # If there is no .idata section then it seems the imports are in the
        # .rdata instead (citation needed).
        import_section = next(
            section for section in parsed_file.sections
            if section.name == '.rdata')

    def rva_to_file_offset(rva, section=import_section):
        # For ski32.exe this is the identity file offset = rva.
        return rva - section.virtual_address + section.rawdata_pointer

    # If import_directory_entries had all the data, then it should be
    # able to find the names however it starts at where the offset table
    # is. Seems like could do:  start_address=

    import_entries = import_directory_entries.parse(
        raw_data,
        start_address=rva_to_file_offset(import_table.virtualaddress),
    )[1]
    import_entries.pop()  # Remove the last sentinel item.

    # The idea was to add name field to the entries which goes and looks it
    # up. For now manually patch it in.
    for entry in import_entries:
        offset = rva_to_file_offset(entry.name_address)
        entry.name = CString("ascii").parse(raw_data[offset:])

    for entry in import_entries:
        offset = rva_to_file_offset(entry.import_name_table_address)
        table = import_lookup_table.parse(
            raw_data[offset:],
            signature=parsed_file.optionalheader.signature,
        )
        table.pop()  # Remove the last sentinel item.

        print(entry.name)

        if verbose:
            # This essentially matches "dumpbin /import" output sans the
            # whitespace being exact. There is an extra '0x40' at the start.
            print(
                f'{entry.import_address_table_address:>16X} Import Address Table'
                f'\n{entry.import_name_table_address:>16X} Import Name Table'
                f'\n{entry.time_date_stamp:>16} time date stamp'
                f'\n{entry.forwarder_chain:>16} Index of first forwarder reference'
                '\n'
            )

        def is_ordinal(field):
            # TODO: Move this into import_lookup_table
            if parsed_file.optionalheader.signature == 'PE32plus':
                return row & 0x8000000000000000

            return row & 0x80000000

        for row in table:
            if is_ordinal(row):
                ordinal = row & 0xFFFF
                print(f' ' * 16 + f' Ordinal {ordinal:>5}')
            else:
                offset = rva_to_file_offset(row)
                name_entry = hint_name_table_entry.parse(raw_data[offset:])
                print(f'{name_entry.hint:>16X} {name_entry.name}')
        print()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Extract images from a executable')
    parser.add_argument('executables', metavar='FILE', nargs='+',
                        help='an executable file to parse')
    args = parser.parse_args(['ski32.exe'])

    for exe in args.executables:
        parsed_file, resources = parse(exe)

        with open(exe, 'rb') as reader:
            raw_data = reader.read()

        output_bitmaps(raw_data, resources, 'new_output')
        imports(parsed_file, raw_data)
