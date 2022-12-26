/*
    Sean Donnellan
    BubbleSort for Array of Numbers in ANSI C
*/

#include <stdio.h>

void printArray (int numbers[], int len) {
    int i;
    for (i = 0; i < len; i++) {
        printf(" %i", numbers[i]);
    }
    printf("\n");
};

void BubbleSort (int numbers[], int len) {
    int sweep = 0;
    int index;
    /*loop over all position in the array*/
    while (sweep < len) {
        printArray(numbers,len);
        for (index = 0; index < len - 1; index++) {
            /* Compare current item to the next one */
            if (numbers[index] > numbers[index+1]) {
                /* Swap the items around*/
                int temp = numbers[index+1];
                numbers[index+1] = numbers[index];
                numbers[index] = temp;
                printArray(numbers,len);
            }
        }
        sweep = sweep + 1;
    }
};

int main() {
    int numbers[] = {3, 9, 6, 1, 2};
    int len = sizeof(numbers) / sizeof(int);

    printf("Array before sorting:\n");
    printArray(numbers, len);

    /* Sort the array using Bubble Sort*/
    BubbleSort(numbers, len);

    printf("Array after sorting:\n");
    printArray(numbers, len);

    return 0;
};
