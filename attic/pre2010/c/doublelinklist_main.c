
#include "doublelinklist.h"

#include <stdio.h>

int main()
{

  {
    struct List* list = listCreate();
  
    listPushFront(list, 5);
    listPushFront(list, 3);
  
    listPushBack(list, 9);
    listPushBack(list, 10);
  
    printf("List front: %d\n", listPeekFront(list));
    printf("List back: %d\n", listPeekBack(list));
    printf("The list is empty: %s\n", listIsEmpty(list) ? "true" : "false");
 
    listPrint(list);

    struct ListIterator* itU = listBegin(list);
    printf("List going forwards [ ");
    while (itU != NULL)
    {
      int value = listNext(&itU);
      printf("%d ", value);
    }
    printf("]\n");

    struct ListIterator* itV = listEnd(list);
    printf("List going backwards [ ");
    while(itV != NULL)
    {
      int value = listPrevious(&itV);
      printf("%d ", value);
    }
    printf("]\n");

    listDestroy(list);
  }

  {
    // Test using the other constructor
    struct List* list;
    listBuild(&list);

    listPushFront(list, 5);
    listPushFront(list, 3);
  
    listPushBack(list, 9);
    listPushBack(list, 10);
 
    listPrint(list);
    listDestroy(list);
  }

  {
    // Test the is empty method.
    printf("List 2 is empty: %s\n", listIsEmpty(NULL) ? "true" : "false");

    struct List* list = listCreate();
    printf("List 3 is empty: %s\n", listIsEmpty(list) ? "true" : "false");

    listDestroy(list);
  }

  return 0;
}
