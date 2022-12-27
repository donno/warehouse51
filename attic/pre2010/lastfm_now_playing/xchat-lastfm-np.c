/**
    LastFMNP

    Last.FM Now Playing plugin - Announce what your listening to

    \author Sean Donnellan (darkdonno@gmail.com)
    \date   2009-April-1
*/

#include <stdio.h>

#define LEAN_AND_MEAN
#include <windows.h>
#include <psapi.h>


#include "xchat-plugin.h"

#define PNAME "LastFMNP"
#define PDESC "Last.FM Now Playing plugin - Announce what your listening to"
#define PVERSION "0.2"

static xchat_plugin *ph;   /* plugin handle */
static HWND lastfmWindowHandle;

HWND GetLastFMHandle();

static int lfmnp_cb(char *word[], char *word_eol[], void *userdata) {
    TCHAR szBuf[128];
    SendMessage((void *)lastfmWindowHandle, WM_GETTEXT, 80, (LPARAM)szBuf);
    xchat_commandf(ph, "ME is listening to %s", szBuf);
   return XCHAT_EAT_ALL;   /* eat this command so xchat and other plugins can't process it */
}

static int lfmnpset_cb(char *word[], char *word_eol[], void *userdata) {
    sscanf(word[2], "%d", &lastfmWindowHandle);
    xchat_printf(ph, "Set LastFM Window handle to %d", lastfmWindowHandle);
    return XCHAT_EAT_ALL;   /* eat this command so xchat and other plugins can't process it */
}

void xchat_plugin_get_info(char **name, char **desc, char **version, void **reserved) {
   *name = PNAME;
   *desc = PDESC;
   *version = PVERSION;
}

int xchat_plugin_init(xchat_plugin *plugin_handle,
    char **plugin_name, char **plugin_desc, char **plugin_version, char *arg) {
    /* we need to save this for use with any xchat_* functions */
    ph = plugin_handle;

    /* tell xchat our info */
    *plugin_name = PNAME;
    *plugin_desc = PDESC;
    *plugin_version = PVERSION;

    lastfmWindowHandle = GetLastFMHandle();

    xchat_hook_command(ph, "lfmnp", XCHAT_PRI_NORM, lfmnp_cb, "Usage: LFMNP, Last.FM Now Playing", 0);
    xchat_hook_command(ph, "lfmnps", XCHAT_PRI_NORM, lfmnpset_cb, "Usage: LFMNP [windowHandle]  Sets the Window handle for Last.FM", 0);

    xchat_print(ph, "Last.FM - Now Playing Plugin loaded successfully!\n");

   return 1;      /* return 1 for success */
}

HWND GetLastFMHandle() {
    HWND handle;
    DWORD processId = 0;
    int x = 0;
    TCHAR szBuf[128];
    TCHAR szPath[MAX_PATH+1];
    WINDOWINFO wi;

    
    handle = FindWindow("QWidget", NULL);
    while (handle != 0) {
        handle = GetWindow(handle, GW_HWNDNEXT);
        

        if (GetParent(handle) == 0 && GetTopWindow(handle)) {
            if ( GetWindowInfo( handle, &wi ) ) {
                if ((wi.dwStyle & WS_CAPTION) ==  WS_CAPTION) {
                    
                    TCHAR szProcessName[MAX_PATH] = TEXT("<unknown>");

                    //GetModuleBaseNameW ( handle, NULL, szPath, MAX_PATH );
                    HMODULE hMod;
                    DWORD cbNeeded;
                    HANDLE hProcess;

                    GetWindowThreadProcessId(handle, &processId); 
                    hProcess = OpenProcess( PROCESS_QUERY_INFORMATION |
                                   PROCESS_VM_READ,
                                   FALSE, processId );

                    if ( EnumProcessModules( hProcess, &hMod, sizeof(hMod),  &cbNeeded) ) {
                            GetModuleBaseName( hProcess, hMod, szProcessName, 
                               sizeof(szProcessName)/sizeof(TCHAR) );
                        if (strcmp("LastFM.exe", szProcessName) == 0) {
                            return handle;
                        }
                    }
                }
                
            }
            
        }
    }
    return 0; // Handle 0 == IDLE so yeh ERROR
}

int main() {
    TCHAR szBuf[128];
    
    lastfmWindowHandle = GetLastFMHandle();
    printf("XChat now playing via LastFM: %d\n", lastfmWindowHandle);

    /*SendMessage(lastfmWindowHandle, WM_GETTEXT, 80, (LPARAM)szBuf);
    printf("ME is listening to %s\n", szBuf);*/
    return 0;
}
