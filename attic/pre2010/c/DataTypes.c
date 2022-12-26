
#include <stdio.h>

struct PlayerStats {
    int mass;
    int speed;
};

struct Player {
    const char * name;
    int x;
    int y;
    int damage;
    short d; /* use numpad mapping */
    short n;
    int mass;
    int speed;
    int moves;
} Player;

static int currentPlayerN = 1;

void printPlayer(struct Player p) {
    printf("Player-%d\nName:\t%s\n", p.n, p.name);
}

void createPlayer(struct Player * p, const char * name) {
    p->name = name;
    p->x = 0;
    p->y = 0;
    p->n = currentPlayerN;
    currentPlayerN++;
}

int main() {
    printf("DataType: TestBed\n");   
    printf("CreatePlayer\n");
    struct Player p1;
    struct Player p2;
    createPlayer(&p1, "Donkey Kong");
    createPlayer(&p2, "Samus");
    printPlayer(p1);
    printPlayer(p2);
    return 0;
}

void printAllPlayerNames() {
    
}
/* Player selection screen */
