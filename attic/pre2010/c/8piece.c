#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define BOARD_WIDTH 3
#define BOARD_SIZE BOARD_WIDTH*BOARD_WIDTH

struct Board {
	int cells[BOARD_SIZE];
	int blankPosition;
};

void populateBoard(struct Board* board)
{
	int randBoard[BOARD_SIZE];

	unsigned int i;
	for ( i = 0; i < BOARD_SIZE; ++i)
	{
		randBoard[i] = i + 1;
	}

	srand(time(NULL));

	for (i = BOARD_SIZE; i > 0; --i)
	{
		unsigned int j;
		int idx = rand() % i;

		board->cells[i - 1] = randBoard[idx];

    if (randBoard[idx] == 9)
    {
      board->blankPosition = i - 1;
    }

		for (j = idx+1; j <= i; ++j)
		{
			// copy remaining items to the bottom of the list
			randBoard[j-1] = randBoard[j];
		}
	}
}

void printBoard(struct Board* board) {
	unsigned int i, j;
	for ( i = 0, j = 1;
		 i < BOARD_WIDTH * BOARD_WIDTH; ++i, ++j)
	{
		printf("%d ", board->cells[i]);
		if (j == 3){
			j = 0;
			puts("\n");
		}
	}
}

struct Board* createMove(struct Board* source, int move)
{
  // Perform move
  int firstPosition;
  int secondPosition;

  int blank = source->blankPosition
  switch (move)
  {
    case 8:
      if (source->blankPosition < BOARD_WIDTH) return NULL;
      break;
    case 2:
      if (source->blankPosition > BOARD_SIZE-BOARD_WIDTH) return NULL;
      break;
    
    case 4: // if 0, 3, 6 on a 3x3
      if (source->blankPosition % BOARD_WIDTH) return NULL;
      firstPosition = 
      break;
    case 7: // if 2, 5, 8 on a 3x3
      if ((source->blankPosition - BOARD_WIDTH - 1) % BOARD_WIDTH) return NULL;

      break;
  }

  struct Board* newBoard;
  newBoard = (struct Board*)malloc(sizeof(struct Board));
  memcpy(newBoard, source, sizeof(source));
  
}

void isSolved(struct Board* board)
{
	int i;
	for ( i = 0; i < BOARD_SIZE; ++i) {
		if (board[i] != i +1){
			return false;
		}
	}
	return true;
}

struct QueueInternal
{
	struct Board* board;
	struct QueueInternal* next;
};

void bfs(struct Board* start)
{
  struct QueueInternal qs;
  qs.next = NULL;

	struct QueueInternal* head;
  head = &qs;
  
  for (;head != NULL; head = head->next)
  {

  }
  printf("Done");
}

int main() {
	struct Board board;
	populateBoard(&board);
	printBoard(&board);
  bfs(&board);
	return 0;
}
