////////////////////////////////////////////////////////////////////////////////
//
// A simple doubly linked list implementation in C
//
// AUTHOR: Donno (darkdonno@gmail.com)
//
////////////////////////////////////////////////////////////////////////////////

#include <assert.h>
#include <stdlib.h>

////////////////////////////////////////////////////////////////////////////////
// The plain old data structures used internally by this module.
////////////////////////////////////////////////////////////////////////////////
struct List
{
  struct Item* head;
  struct Item* tail;
};

struct Item
{
  int value;
  struct Item* next;
  struct Item* prev;
};

typedef struct Item ListIterator;

////////////////////////////////////////////////////////////////////////////////
// The implementation of the list functions.
////////////////////////////////////////////////////////////////////////////////
struct List* listCreate()
{
  struct List* list = (struct List*)malloc(sizeof(struct List));
  list->head = NULL;
  list->tail = NULL;
  return list;
}

void listBuild(struct List** list)
{
  *list = listCreate();
}

void listDestroy(struct List* list)
{
  struct Item* previous = NULL;
  struct Item* current;
  for(current = list->head; current != NULL; current = current->next)
  {
    free(previous);
    previous = current;
  }
}

void listPushFront(struct List* list, int value)
{
  struct Item *item = (struct Item*)malloc(sizeof(struct Item));
  item->value = value;
  item->prev = NULL;
  item->next = list->head;

  // Tail can not be null if the had is not.
  if (list->head != NULL)
  {
    list->head->prev = item;
  }
  else
  {
    // If head is null then tail should be as well.
    assert(list->tail == NULL);
    list->tail = item;
  }

  list->head = item;
}

void listPushBack(struct List* list, int value)
{
  struct Item *item = (struct Item*)malloc(sizeof(struct Item));
  item->value = value;
  item->prev = list->tail;
  item->next = NULL;
  if (list->head == NULL)
  {
    assert(list->tail == NULL);
    list->head = item;
  }
  else
    {
      list->tail->next = item;

    }

  list->tail = item;
}

int listIsEmpty(struct List* list)
{
  return list == NULL || list->head == NULL;
}

int listPeekFront(struct List* list)
{
  assert(list->head != NULL);
  return list->head->value;
}

int listPeekBack(struct List* list)
{
  assert(list->tail != NULL);
  return list->tail->value;
}

ListIterator* listBegin(struct List* list)
{
  if (!list) {
    return NULL;
  }

  return list->head;
}

ListIterator* listEnd(struct List* list)
{
  if (!list) {
    return NULL;
  }

  return list->tail;
}

int listNext(ListIterator** iterator)
{
  assert(iterator != NULL);
  assert(*iterator != NULL);

  int value = (*iterator)->value;
  *iterator = (*iterator)->next;
  return value;
}

int listPrevious(ListIterator** iterator)
{
  assert(iterator != NULL);
  assert(*iterator != NULL);

  int value = (*iterator)->value;
  *iterator = (*iterator)->prev;
  return value;
}

int listValue(ListIterator* iterator)
{
  assert(iterator != NULL);
  return iterator->value;
}

void listPrint(struct List* list)
{
  struct Item* current;
  printf("List [Forward]: ");
  for(current = list->head; current != NULL; current = current->next)
  {
    printf("%d ", current->value);
  }
  printf("\n");
do
  printf("List [Backwards]: ");
  for(current = list->tail; current != NULL; current = current->prev)
  {
    printf("%d ", current->value);
  }
  printf("\n");
}
