"""Parse the Microsoft Portable Executable and Common Object File Format.

The use of the Construct library (http://construct.readthedocs.org/) is used to
facility defining the structures used in the file format which can then be
used to parse an executable.

The specification for the format can be found here:
  https://msdn.microsoft.com/en-us/windows/hardware/gg463119.aspx
This will be referred to as the specification document here.

For a more complete implementation see the 'formats/executable/pe32.py' file
in the Construct library (https://github.com/construct/construct/), most of the
following was written without refering to this file as I only found it a week
after. At the time of writing it does not provide the
Resource[Data|Directory]Entry struct.

LICENSE      : The MIT License (see LICENSE.txt for details)

TODO         :
  - Parse the rest of the format, at the moment it only does the parts that I
    was interested in at the time.
  - Take more advantage of Construct such that its possible to do pe.parse(data)
    and it can resolve all the structures etc.

"""

from construct import *

# The following was inspired from
# http://en.wikibooks.org/wiki/X86_Disassembly/Windows_Executable_Files
# with naming from http://llvm.org/docs/doxygen/html/Object_2COFF_8h_source.html
DosHeader = Struct("DOSHeader",
  Const(Field("Signature", 2), "MZ"),
  SLInt16("LastSize"),
  SLInt16("BlockCount"),
  SLInt16("ReallocationCount"),
  SLInt16("HeaderSize"),
  SLInt16("MinAlloc"),
  SLInt16("MaxAlloc"),
  SLInt16("InitialRelativeSS"),
  SLInt16("InitialSP"),
  SLInt16("Checksum"),
  SLInt16("InitialIP"),
  SLInt16("InitialRelativeCS"),
  SLInt16("RelocationTableAddress"),
  SLInt16("OverlayCount"),
  Array(4, SLInt16("Reserved1")),
  SLInt16("OemID"),
  SLInt16("OemInfo"),
  Array(10, SLInt16("Reserved2")),
  SLInt32("NewExeHeaderAddress"),
  )

# MachineType specifies the CPU type that the code within the image can be
# executed on.
MachineType = Enum(SLInt16("ID"),
  UNKNOWN	= 0x0,	  # This is applicable to any machine type.
  AM33	= 0x1d3,    # Matsushita AM33
  AMD64	= 0x8664,   # x64
  ARM	= 0x1c0,      # ARM little endian
  ARMNT	= 0x1c4,    # ARMv7 (or higher) Thumb mode only
  ARM64	= 0xaa64,   # ARMv8 in 64-bit mode
  EBC	= 0xebc,      # EFI byte code
  I386	= 0x14c,	  # Intel 386 or later processors and compatible processors
  IA64	= 0x200,	  # Intel Itanium processor family
  M32R	= 0x9041,	  # Mitsubishi M32R little endian
  MIPS16	= 0x266,	# MIPS16
  MIPSFPU	= 0x366,	# MIPS with FPU
  MIPSFPU16	= 0x466,# MIPS16 with FPU
  M68K = 0x268,     # Motorola 68000 series
  POWERPC	= 0x1f0,	# Power PC little endian
  POWERPCFP	= 0x1f1,# Power PC with floating point support
  R4000	= 0x166,	  # MIPS little endian
  SH3	= 0x1a2,	    # Hitachi SH3
  SH3DSP	= 0x1a3,	# Hitachi SH3 DSP
  SH4	= 0x1a6,	    # Hitachi SH4
  SH5	= 0x1a8,	    # Hitachi SH5
  PureMSIL = 0xc0ee,# Pure MSIL for the Common Language Runtime (CLR).
  )

# Specificies certain characteristics of the image file.
PECharacteristics = FlagsEnum(
  SLInt16("Characteristics"),
  RelocsStripped	     = 0x0001, # Indicates that the file does not contain base
                                 # relocations and must therefore be loaded at
                                 # its preferred base address.
  ExecutableImage  	   = 0x0002, # Image only. This indicates that the image
                                 # file is valid and can be run. If this flag is
                                 # not set, it indicates a linker error.
  LineNumbersStripped  = 0x0004, # This flag is deprecated and should be zero.
  LocalSymbolsStripped = 0x0008, # This flag is deprecated and should be zero.
  AggressiveWSTrim	   = 0x0010, # This flag is obsolete and should be zero.
  LargeAddressAware    = 0x0020, # Application can handle > 2 GB addresses.
  Reserved             = 0x0040, # This flag is reserved for future use.
  )

# Based on http://geezer.osdevbrasil.net/osd/exec/pe.txt and
# https://msdn.microsoft.com/en-us/library/windows/desktop/ms680336.aspx
peHeaderBase = Struct("PEHeader",
  Const(Field("Signature", 4), "PE\0\0"),
  MachineType,
  SLInt16("SectionCount"),
  SLInt32("DateTimeStamp"),
  SLInt32("SymbolTableFileOffset"),
  SLInt32("SymbolCount"),
  SLInt16("OptionHeaderSize"),
  PECharacteristics,
  )

# This is section 2.4.1 Optional Header Standard Fields in the MPECOFF
# specification document.
peHeaderOptional = Struct("PEHeaderOptional",
  Const(SLInt16("Magic"), 0x010B),
  SLInt8("MajorLinkerVersion"),
  SLInt8("MinorLinkerVersion"),
  SLInt32("CodeSize"), # The size of the code (text) section or sum of them.
  SLInt32("InitializedDataSize"),
  SLInt32("UnitializedDataSize"),
  SLInt32("EntryPointAddress"),
  SLInt32("CodeBaseAddress"),
  SLInt32("DataBaseAddress"),

  # The preferred address of the first byte of image when loaded into memory
  SLInt32("ImageBaseAddres"),

  SLInt32("SectionAlignment"),
  SLInt32("FileAlignment"),
  SLInt16("MajorOperatingSystemVersion"),
  SLInt16("MinorOperatingSystemVersion"),
  SLInt16("MajorImageVersion"),
  SLInt16("MinorImageVersion"),
  SLInt16("MajorSubSystemVersion"),
  SLInt16("MinorSubSystemVersion"),
  SLInt32("Win32VersionValue"),  # This is reserved and should be zero.
  SLInt32("ImageSize"),
  SLInt32("HeadersSize"),
  SLInt32("CheckSum"),
  SLInt16("Subsystem"),  # TODO: Replace this with an enumeration.
  SLInt16("DllCharacteristics"),  # TODO: Replace this with a flag.
  SLInt32("StackReserveSize"),
  SLInt32("StackCommitSize"),
  SLInt32("HeapReserveSize"),
  SLInt32("HeapCommitSize"),
  SLInt32("LoadingFlag"), # No longer used.
  SLInt32("RvaAndSizesCount"),

  Array(lambda ctx: ctx.RvaAndSizesCount,
        Struct("DataDirectories",
               ULInt32("Address"),
               ULInt32("Size"),
              )
        ),
  )

# The following list is from 2.4.3. Optional Header Data Directories and
# it corresponds to the elements in peHeaderOptional.DataDirectories.
#
# The intended use is:
#   for name, directory in zip(dataDirectoryIndexToName,
#                              peData.Optional.DataDirectories):
dataDirectoryIndexToName = [
  'ExportTable',
  'ImportTable',
  'ResourceTable',
  'ExceptionTable',
  'CertificateTable',
  'BaseRelocationTable',
  'Debug',
  'Architecture', # Reserved and unused.
  'GlobalPointer',
  'TLSTable', # Thread local storage table address.
  'LoadConfigurationTable',
  'BoundImportTable',
  'ImportAddressTable',
  'DelayImportDescriptor',
  'CLRRuntimeHeader',
  ]

peHeader = Struct("NTImageHeader",
                  Embed(peHeaderBase),
                  Embed(peHeaderOptional))

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms680341.aspx
sectionHeader = Struct(
  "SectionHeader",
  String("Name", 8),
  SLInt32("VirtualSize"),
  SLInt32("VirtualAddress"),
  SLInt32("RawDataSize"),
  SLInt32("RawDataPointer"),
  SLInt32("RelocationPointer"),
  SLInt32("LineNumberPointer"),
  SLInt16("RelocationCount"),
  SLInt16("LineNumberCount"),
  SLInt32("Characteristics"),
  )

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms648009.aspx
# ID 13, 15 and 18 are missing.
#
ResourceID = Enum(SLInt32("ID"),
  Cursor = 1,
  Bitmap = 2,
  Icon = 3,
  Menu = 4,
  DialogBox = 5,
  StringTableEntry = 6,
  FontDirectory = 7,
  Font = 8,
  AcceleratorTable = 9,
  RawData = 10,
  MessageTableEntry = 11,
  GroupCursor = 12,
  GroupIcon = 14,
  VersionInformation = 16,
  DlgInclude = 17,
  PlugAndPlay = 19,
  VXD = 20,
  AnimatedCursor = 21,
  AnimatedIcon = 22,
  HTML = 23,
  AssemblyManifest = 24,
  _default_ = Pass,
  )

ResourceIDEntry = Struct(
  "ResourceIDEntry",
  ResourceID,
  ULInt32("Offset"),
  )

ResourceDirectoryTable = Struct(
  "ResourceDirectoryTable",
  SLInt32("Characteristics"),
  SLInt32("DateTimeStamp"),
  SLInt16("MajorVersion"),
  SLInt16("MinorVersion"),
  SLInt16("NameEntryCount"),
  SLInt16("IDEntryCount"),
  Array(lambda ctx: ctx.IDEntryCount, ResourceIDEntry),
  )

ResourceDataEntry = Struct(
  "ResourceDataEntry",
  ULInt32("Offset"),
  ULInt32("Size"),
  ULInt32("CodePage"),
  ULInt32("Reserved"),
  )

StringTable = Struct(
  "StringTable",
  ULInt16("Length"),
  ULInt16("ValueLength"),
  ULInt16("Type"),
  ULInt8("Key"),
  ULInt16("Padding"),
  )

# Begin structures for parsing the .idata section (also known as the import
# tables).
ImportDirectoryEntry = Struct(
  "ImportDirectoryEntry",
  ULInt32("ImportNameTableAddress"),
  ULInt32("TimeDateStamp"),
  ULInt32("ForwarderChain"),
  ULInt32("NameAddress"),
  ULInt32("ImportAddressTableAddress"),
  )

# The 31st bit decides if it is import by ordinal (1) or by name (0).
#
# See for how to implement this properly,
#  http://construct.readthedocs.org/en/latest/bitwise.html#bitfield
# For now I have only been working with entries with are by name.
NameTableEntries = RepeatUntil(lambda v, ctx: v == 0, ULInt32("Value"))

HintNameTableEntry = Struct(
  "HintNameTableEntry",
  ULInt16("Hint"),
  CString('Name'),
  )

# TODO: I am quite sure that the Construct library allows this to be chained
# into one thing were the values in NameTableEntries are automatically resolved
# to HintNameTableEntry.

# End of structures for parsing the .idata section.

def parse(filename):
  """This function is very specialised at the moment as it was aimed at only
  doing the operation I was looking for. It aims at finding the resource
  section and finds the bitmaps in it.

  I also don't believe its general enough to find all bitmaps that are stored
  in the resource section of any executable.
  """

  # Read the whole file.
  with open(filename, 'rb') as fr:
    data = fr.read()

  dosData = DosHeader.parse(data)
  peData = peHeader.parse(data[dosData.NewExeHeaderAddress:])

  sectionHeaderStartAddress = (dosData.NewExeHeaderAddress +
                               peHeaderBase.sizeof() +
                               peData.OptionHeaderSize)

  SectionHeaders = Array(peData.SectionCount, sectionHeader)

  sectionHeaders = SectionHeaders.parse(data[sectionHeaderStartAddress:])

  # The following is where
  # Attempt to parse the resource section (.rsrc).
  resourceSection = [
    section for section in sectionHeaders
    if section.Name.startswith('.rsrc')][0]

  entries = ResourceDirectoryTable.parse(data[resourceSection.RawDataPointer:])

  # Print the IDs and Offsets of the first resource directory.
  #
  # Note: The following assumes these entries point to more directories, which
  # is indicated by the most signification bit of entry.Offset being 1.
  print [(entry.ID, '%08x' % (entry.Offset ^ (1 << 31)))
          for entry in entries.ResourceIDEntry]

  # In the executable this was developed on it had an entry specificially for
  # Bitmaps, based on the specification this doesn't seem like it has to be the
  # case.
  offset = [e.Offset for e in entries.ResourceIDEntry if e.ID == 'Bitmap'][0]
  offset = offset ^ (1 << 31)
  bitmapTableEntryAddress = (resourceSection.RawDataPointer + offset)

  bitmapTableEntries = ResourceDirectoryTable.parse(
    data[bitmapTableEntryAddress:])

  directories = peData.DataDirectories

  nameToDirectory = dict(
    (name, directory)
    for name, directory in zip(dataDirectoryIndexToName, directories)
    if directory.Address != 0 and directory.Size != 0
    )

  # Parse the import directory table if it exists.
  importDirectoryEntries = []
  if 'ImportTable' in nameToDirectory:
    importTableAddress = nameToDirectory['ImportTable'].Address
    while True:
      entry = ImportDirectoryEntry.parse(data[importTableAddress:])

      # Keep going until there is a 'null' entry.
      if (entry.ImportNameTableAddress == 0 and entry.TimeDateStamp == 0 and
          entry.ForwarderChain == 0 and entry.NameAddress == 0 and
          entry.ImportAddressTableAddress == 0):
        break

      importDirectoryEntries.append(entry)
      importTableAddress += ImportDirectoryEntry.sizeof()

    # Look-up the names of the exports.
    # NOTE: This is assuming they are loaded by name and not ordinal.
    for e in importDirectoryEntries:
      entries = [
        HintNameTableEntry.parse(data[entry:])
        for entry in NameTableEntries.parse(data[e.ImportNameTableAddress:])
        if entry != 0]
      e.Names = entries

  return {
    'dosHeader': dosData,
    'peHeader': peData,
    'sectionHeaders': sectionHeaders,
    'resourceSection': resourceSection,
    'resourceDirectoryTable': entries,
    'bitmapDirectoryTable': bitmapTableEntries,
    'dataDirectoryNameToDirectory': nameToDirectory,
    'importDirectoryEntries': importDirectoryEntries,
    'rawData': data,
  }


def outputBitmaps(data, bitmapTableEntries, resourceSectionDataPointer):
  offsets = [resourceSectionDataPointer + (entry.Offset ^ (1 << 31))
             for entry in bitmapTableEntries.ResourceIDEntry]

  import os
  try:
    os.mkdir('output')
  except OSError:
    pass

  bmpHeader = [0x42, 0x4D, 0x76, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x76,
               0x00, 0x00, 0x00]
  bmpHeader = ''.join(chr(o) for o in bmpHeader)

  i = 0
  for offset in offsets:
    subEntries = ResourceDirectoryTable.parse(data[offset:])
    offsets = [resourceSectionDataPointer + (entry.Offset)
               for entry in subEntries.ResourceIDEntry]

    for entryOffset in offsets:
      resource = ResourceDataEntry.parse(data[entryOffset:])
      entryData = data[resource.Offset : resource.Offset + resource.Size]

      # Write out the bitmap data to files.
      # i could instead be the ID of the bitmap (i.e resource.ID) which in this
      # case is just an integer not an enumeration (ResourceID).
      with open('output/file_%04d.bmp' % i, 'wb') as fw:
        fw.write(bmpHeader)
        fw.write(entryData)

      i = i + 1

if __name__  == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('executables', metavar='FILE', nargs='+',
                      help='an executable file to parse')
  args = parser.parse_args()

  for exe in args.executables:
    parseResults = parse(exe)

    outputBitmaps(parseResults['rawData'],
                  parseResults['bitmapDirectoryTable'],
                  parseResults['resourceSection'].RawDataPointer,
                  )
