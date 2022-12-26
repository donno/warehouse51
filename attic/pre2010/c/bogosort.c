/*
    Simple implementation of BogoSort

    By Sean Donno (darkdonno@gmail.com)
*/

#include <stdio.h>
//#include <stdlib.h>
#include <time.h>

#define USE_DATA(x) int *data = data##x;int data_size = data_size##x

// Data Set 1
int data1[]    = {79, 74, 37, 29, 39, 82, 4, 56, 59, 9, 26, 86, 39, 52, 57, 6, 64, 8, 42, 12, 66, 63, 14, 87, 98, 85, 90, 97, 16, 99, 60, 95, 72, 96, 24, 11, 77, 27, 66, 36, 36, 91, 21, 74, 43, 78, 80, 6, 86, 22, 18, 52, 84, 31, 38, 82, 15, 28, 78, 31, 27, 37, 26, 99, 32, 49, 9, 9, 76, 75, 45, 11, 66, 66, 85, 8, 44, 65, 14, 30, 86, 31, 81, 70, 62, 19, 51, 77, 47, 28, 8, 73, 64, 33, 71, 96, 82, 79, 5, 57};
#define data_size1 100

// Data Set 2
int data2[]    = {5,2,6,1};
#define data_size2 4

USE_DATA(2);

/* int isSorted(int array[], int arraySize) { */
/*     unsigned int i; */

/*     for ( i = 0; i < arraySize - 1; i++ ){ */
/*         if ( array[i] > array[i+1] ) { */
/*             return 1; */
/*         } */
/*     } */

/*     return 0; */
/* } */

/* void shuffle(int array[], int arraySize ) { */
/*     if (arraySize > RAND_MAX) { */
/*         puts("ERROR: CAN NOT HANDLE arrays larger than RAND_MAX"); */
/*         return; */
/*     } */

/*     int i, j, tmp; */

/*     for ( i = arraySize - 1; i > 1; i--) { */
/*         j = rand() % i; */
/*         tmp = array[i]; */
/*         array[i] = array[j]; */
/*         array[j] = tmp; */
/*     } */
/* } */


/**
    Performs bogosort using a helper

    \param array the array to sort
    \param arraySize the size of the array
*/
/* void bogosortWithHelp(int array[], int arraySize) { */
/*     while ( isSorted(data, data_size) != 0 ) { */
/*         shuffle(data, data_size); */
/*     } */
/* } */

#define data_size1 100

#define RAND_INT_MAX 0x7fff

//int data2[]    = {5,2,6,1};
//#define data_size2 4

static unsigned long long randomSeed = 0;


// Portability

/**

   For Windows:
     RtlGenRandom or CryptGenRandom
 */

#ifdef _WIN32

#define DIFFTIME 0x19db1ded53e8000ULL

typedef unsigned long DWORD;
typedef int INT, LONG;
typedef long long LONGLONG;

typedef unsigned long ULONG;
typedef unsigned long long ULONGLONG;
//typedef unsigned long *LPDWORD;
typedef unsigned long * LPDWORD;

#if defined(_WIN64)
 typedef unsigned __int64 ULONG_PTR;
#else
 typedef unsigned long ULONG_PTR;
#endif

typedef const void *LPCVOID;
typedef void *HANDLE;


 typedef struct _OVERLAPPED {
     ULONG_PTR Internal;
     ULONG_PTR InternalHigh;
     DWORD Offset;
     DWORD OffsetHigh;
     HANDLE hEvent;
 } OVERLAPPED,*POVERLAPPED,*LPOVERLAPPED;


typedef union _ULARGE_INTEGER {
    struct {
	ULONG LowPart;
	ULONG  HighPart;
    };
    struct {
	DWORD LowPart;
	ULONG  HighPart;
    } u;
    ULONGLONG QuadPart;
} ULARGE_INTEGER;

typedef struct _FILETIME {
    DWORD dwLowDateTime;
    DWORD dwHighDateTime;
} FILETIME, *PFILETIME, *LPFILETIME;


__stdcall GetSystemTimeAsFileTime(LPFILETIME lpSystemTimeAsFileTime);
HANDLE __stdcall GetStdHandle( DWORD nStdHandle );
int __stdcall WriteFile(
    HANDLE hFile,
    LPCVOID lpBuffer,
    DWORD nNumberOfBytesToWrite,
    LPDWORD lpNumberOfBytesWritten,
    LPOVERLAPPED lpOverlapped
);

/* char * itoa (int value, char* str, int base) */
/* { */
/*     return str; */
/* } */

time_t timenow()
{
    FILETIME SystemTime;
    ULARGE_INTEGER ULargeInt;

    GetSystemTimeAsFileTime(&SystemTime);

    ULargeInt.LowPart = SystemTime.dwLowDateTime;
    ULargeInt.HighPart = SystemTime.dwHighDateTime;
    ULargeInt.QuadPart -= DIFFTIME;
    return (time_t)(ULargeInt.QuadPart / 10000000);
}

// _CRTIMP FILE * __cdecl __iob_func(void);
// On Windows: stdout is __iob_func()[1]
// Need to wrap this to go from Handle to FILE*
/*
#undef stdout
#define stdout GetStdHandle(STD_OUTPUT_HANDLE)
 #define outc(_c,_stream)  (--(_stream)->_cnt >= 0			\
    ? 0xff & (*(_stream)->_ptr++ = (char)(_c)) :  _flsbuf((_c),(_stream))) */

#define STD_OUTPUT_HANDLE   (DWORD)(0xfffffff5)
void outc(char ch)
{
    DWORD NumberOfCharsWritten;

    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),&ch,1,&NumberOfCharsWritten,NULL);
}

void outstr(char* string)
{
    DWORD NumberOfCharsWritten;
    int stringLength;
    const char* text = string;;
    for (stringLength = 0; *text != '\0' ; ++text, ++stringLength);

    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),string, stringLength,
	      &NumberOfCharsWritten, NULL);
}
#undef STD_OUTPUT_HANDLE
#undef DIFFTIME

#else
#define timenow
time_t timenow() { return time(NULL); }
#define outc putchar

void outstr(char* string)
{
    while (*string) outc(*string++);
}

#endif

int randInt(void)
{
#if defined(__GNUC__)
    randomSeed = randomSeed * 0x5deece66dLL + 11;
#else
//    randomSeed = randomSeed * 0x5deece66di64 + 11;
    randomSeed = randomSeed * 0x5deece66d + 11;
#endif
    return (int)((randomSeed >> 16) & RAND_INT_MAX);
}

/**
   Performs bogosort

   \param array the array to sort
   \param arraySize the size of the array
*/
void bogosort(int array[], int arraySize) {
    int i, j, tmp;

    goto check;

notsorted:
    // Peforms the shuffle
    for ( i = arraySize - 1; i > 1; i--) {
        j = randInt() % i;
        tmp = array[i];
        array[i] = array[j];
        array[j] = tmp;
    }

check:
    // Check if its sorted
    for ( i = 0; i < arraySize - 1; i++ ){
        if ( array[i] > array[i+1] ) {
            goto notsorted; // it is not sorted so shuffle
        }
    }

   // Sorting is complete
}

int main() {
    int i;
    char intStr[sizeof(int) * 3];

    randomSeed = timenow();

    outstr("Before: ");

    for ( i = 0; i < data_size; i++ ){
	itoa(data[i], &intStr, 10);
	outstr( intStr );
	outc(' ');
    }
    outc('\n');

    bogosort(data, data_size);

    outstr("After: ");
    for ( i = 0; i < data_size; i++ ){
	itoa(data[i], &intStr, 10);
	outstr( intStr );
	outc(' ');
    }
    outc('\n');

    return 0;
}
