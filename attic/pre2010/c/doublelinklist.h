#ifndef IG__DOUBLE_LINKED_LIST_H_411E6C0A1B83
#define IG__DOUBLE_LINKED_LIST_H_411E6C0A1B83

////////////////////////////////////////////////////////////////////////////////
//
// A simple doubly linked list implementation
//
// AUTHOR: Donno (darkdonno@gmail.com)
//
////////////////////////////////////////////////////////////////////////////////

struct List; // Forward declaration.
struct ListIterator;

////////////////////////////////////////////////////////////////////////////////
// The list functions
////////////////////////////////////////////////////////////////////////////////
struct List* listCreate();
void listBuild(struct List** list);
void listDestroy(struct List* list);

// Insertion operations
void listPushFront(struct List* list, int value);
void listPushBack(struct List* list, int value);

// Get/query operations
int listIsEmpty(struct List* list);
int listPeekFront(struct List* list);
int listPeekBack(struct List* list);

struct ListIterator* listBegin(struct List* list);
struct ListIterator* listEnd(struct List* list);

// Returns the current value from where the iterator points, and 
// increments the iterator.
int listNext(struct ListIterator** iterator);

// Returns the current value from where the iterator points, and 
// decrements the iterator.
int listPrevious(struct ListIterator** iterator);

// Returns the current value where the iterator points to.
int listValue(struct ListIterator* iterator);

// Misc. operation
void listPrint(struct List* list);

////////////////////////////////////////////////////////////////////////////////
#endif
