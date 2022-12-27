#include <hal/input.h>
#include <hal/xbox.h>
#include <openxdk/debug.h>

#include "string.h"
#include "stdio.h"
#include <stdlib.h>


void XBoxStartup(void) {
    int i,done=0;

    XInput_Init();

    debugPrint("Hello world!\n");
    debugPrint("Press B to stop program\n");

    while(!done) {
        XInput_GetEvents();

        for(i=0; i<4; i++)
        {
            if(g_Pads[i].PressedButtons.ucAnalogButtons[XPAD_B]) done=1;
        }
    };

    debugPrint("Bye...\n");

    XInput_Quit();

    XSleep(5000);
    XReboot();
}
