// Source:
// ESRI Shapefile Technical Description
// An ESRI White Paper - July 1998
// http://www.esri.com/library/whitepapers/pdfs/shapefile.pdf

// There are three files, 
//   .shp - Shapefile projects
//   .shx - Spatial index
//   .dbf - dBase table.


// SHP
//
// Fixed-length file header.
// 
#include <string>
#include <stdint.h>
#include <stdio.h>

#include <iostream>



static uint32_t SwapUnsignedInt(uint32_t source)
{
  return (uint32_t)(((source & 0x000000FF << 24)
		     | ((source & 0x0000FF00) << 8)
		     | ((source & 0x00FF0000) >> 8)
		     | ((source & 0xFF000000) >> 24)));
}
    
// Shape types is really enumeration
namespace E_ShapeType
{
  enum Type
  {
    Null = 0,
    Point = 1,
    PolyLine = 3,
    Polygon = 5,
    MultiPoint = 8,
    PointZ = 11,
    PolyLineZ = 13,
    MultiPointZ = 18,
    PointM = 21,
    PolyLineM = 23,
    PolygonM = 25,
    MultiPointM = 28,
    MultiPatch = 31
  };
}

// The byte order used for the following fields are big endian.
struct S_RecordHeader
{
  int32_t myRecordNumber;
  // Record numbers start at 1.

  uint32_t myContentLength;
  // The number of 16-bit words in the record contents section.
  // That is to say the number of 16-bit words after this header.
};

typedef double Tfloat64;
typedef bool Tbool;

struct S_Extent2d
{
  double min;
  double max;
};

struct geoS_Point
{
  double myX;
  double myY;
  double myZ;

  geoS_Point()
    {
    }

  geoS_Point(double X, double Y, double Z)
    : myX(X), myY(Y), myZ(Z)
    {
    }
};




// The packing is only designed for allowing fread and potentially fwrite.
#pragma pack(push,1)
struct S_EsriShapefileProjectHeader
{
  int32_t fileCode; // Always hex value 0x0000270a - Big endian.
  uint32_t unused[5];
  uint32_t fileLength;
  uint32_t version;
  uint32_t shapeType;

  // Next up bounding boxes.
  Tfloat64 myBoundaryXMin;
  Tfloat64 myBoundaryYMin;
  Tfloat64 myBoundaryXMax;
  Tfloat64 myBoundaryYMax;
  Tfloat64 myBoundaryZMin;
  Tfloat64 myBoundaryZMax;
  Tfloat64 myBoundaryMMin;
  Tfloat64 myBoundaryMMax;

  Tbool IsBigEndian() const
    { 
      return fileCode == 0x0000270a;
    }
};
#pragma pack(pop)


struct S_PolygonRecordHeader
{
  uint32_t myShapeType; // This should be a 5.
  Tfloat64 myBox;
  uint32_t myPartCount;
  uint32_t myPointCount;
};

struct C_EsriShapeFilePointIterator
{

  C_EsriShapeFilePointIterator()
    : myFile(NULL)
    {
    }

  C_EsriShapeFilePointIterator(FILE* File, 
			       const S_EsriShapefileProjectHeader& Header)
    :  myHeader(Header),
       myFile(File)
    {
      // Setup back to the start just past the header.
      //
      // This now reads the records and extracts out the points.
      fseek(myFile, 100, SEEK_SET);

      // Read the first record.
      S_RecordHeader recordHeader;
      fread(&recordHeader, sizeof(recordHeader), 1, myFile);
      
      //    if (myHeader.IsBigEndian())
      {
	printf("Big: recordHeader: %d %d\n", recordHeader.myRecordNumber,
	       recordHeader.myContentLength);
      }
//      else
      {
	printf("Lit: recordHeader: %d %d\n", 
	       SwapUnsignedInt(recordHeader.myRecordNumber),
	       SwapUnsignedInt(recordHeader.myContentLength));
      }
    }

  geoS_Point& operator *();

  geoS_Point* operator ->()
    {
      return &myPoint;
    }

  C_EsriShapeFilePointIterator& operator ++()
    {
      return *this;
    }

  bool operator !=(const C_EsriShapeFilePointIterator& That) const
  {
    //if (myFile != That.myFile)
    {
      // 
      // if (myFile && That.myFile)
      // {
      // 	return true;
      // }
      // else if (myFile)
      // {
      //}
    }
    return true;
  }

  const S_EsriShapefileProjectHeader myHeader;
  geoS_Point myPoint;
  FILE* myFile;
};

class EsriShapefileReader
{
public:
  EsriShapefileReader(const std::string& File);
  // This should be a sysC_Path.

  ~EsriShapefileReader();

  bool IsValid() const;

  // Point iterator.
  C_EsriShapeFilePointIterator PointsBegin()
    {
      return C_EsriShapeFilePointIterator(myFile, myHeader);
    }
  C_EsriShapeFilePointIterator PointsEnd() {
    return C_EsriShapeFilePointIterator();
  }

private:

  bool IsBigEndian() const;

  FILE* myFile;
  S_EsriShapefileProjectHeader myHeader;
};


bool EsriShapefileReader::IsValid() const
{
  if (myHeader.fileCode != 0x0000270a &&
      myHeader.fileCode != 0x0a270000)
  {
    return false; // File code (magic number) doesn't match.
  }

  if (IsBigEndian())
  {
    if (myHeader.version != 0xe8030000)
    {
      return false;
    }
  }
  else
  {
    if (myHeader.version != 1000)
    {
      return false;
    }
  }

  return true;
}

bool EsriShapefileReader::IsBigEndian() const
{
  // ASSERT( IsValid() )
  return myHeader.fileCode == 0x0000270a;
}

EsriShapefileReader::EsriShapefileReader(
  const std::string& File)
{
  myFile = fopen(File.c_str(), "rb");
  
  fread(&myHeader, sizeof(myHeader), 1, myFile);

  const bool isBigEndian =
    (myHeader.fileCode == 0x0000270a);

  if (!isBigEndian && myHeader.fileCode != 0x0a270000)
  {
    // The file code didn't match.
    // Throw.
    return;
  }


  printf("%s\n", (IsValid() ? "true" : "false"));

  printf("%d\n", myHeader.shapeType);
}

EsriShapefileReader::~EsriShapefileReader()
{
  fclose(myFile);
}

int main()
{
  // This is only required if you want to fwrite/fread the header,
  // all at once.
  static_assert( sizeof(S_EsriShapefileProjectHeader) == 100,
		 "The main file header MUST be 100 bytes long." );

  EsriShapefileReader reader("data/cgd109p020.shp");

  for (auto& point = reader.PointsBegin();
       //point != reader.PointsEnd();
       true;
       ++point)
  {
    std::cout << point->myX << " , " << point->myY << std::endl;
    break;
  }
  return 0;
}
