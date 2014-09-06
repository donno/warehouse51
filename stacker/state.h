#ifndef STATE_H_GUARD
#define STATE_H_GUARD

#include <SDL.h>
  
#if _MSC_VER < 1800
#define bool int
#define false 0
#define true 1
#define __bool_true_false_are_defined 1
#else
#include <stdbool.h>
#endif


/**
    A structure for defining a state
*/
struct State {
    void (*funcInit)(void);
    void (*funcDraw)(SDL_Surface *);
    void (*funcEvent)(SDL_Event *);
    void (*funcDeinit)(void);
};

/**
    Get the State, the system is in
    \return the current identifier (int) for the state of the system
*/
int GetState();

/**
    Change from the current state to a new state
    \param	newState	the new state to change to
    \param	cleanState	is this state a clean stat is the current state kept in play
*/
void ChangeState(int newState, bool cleanState);

#define DefSetupState(x)    void SetupState ## x(struct State *state);

#endif
