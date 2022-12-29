/*
 *      Copyright (C) 2007 Sean Donnellan (Donno)
 *      darkdonno@gmail.com
 *
 *  This Program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2, or (at your option)
 *  any later version.
 *
 *  This Program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with GNU Make; see the file COPYING.  If not, write to
 *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
 *  http://www.gnu.org/copyleft/gpl.html
 *
 *
 */

#include <Windows.h>
#define MSN_MAX_LENGTH 256

/*****************************************************************************
 * SendToMSN
 *****************************************************************************/
static void SendToMSN(char *psz_msg ) {
    COPYDATASTRUCT msndata;
    HWND msnui = NULL;
    wchar_t buffer[MSN_MAX_LENGTH];

    mbstowcs( buffer, psz_msg, MSN_MAX_LENGTH );
    msndata.dwData = 0x547;
    msndata.lpData = &buffer;

    msndata.cbData = (lstrlenW(buffer)*2)+2;

    while( ( msnui = FindWindowEx( NULL, msnui, "MsnMsgrUIManager", NULL ) ) )
    {
        SendMessage(msnui, WM_COPYDATA, (WPARAM)NULL, (LPARAM)&msndata);
    }
}

/*****************************************************************************
 * SendtoMsn
 *****************************************************************************/
static void SendtoMsn(const char * type, const char * formatting, const char *info0,const char *info1,const char *info2) {
    char psz_tmp[MSN_MAX_LENGTH];
    snprintf( psz_tmp,MSN_MAX_LENGTH,"\\0%s\\01\\0%s\\0%s\\0%s\\0%s\\0\\0\\0",type,formatting,info0,info1, info2);
    SendToMSN(psz_tmp);
}

int main(int argc, char **argv) {
    printf("Windows Live Messenger::Now Playing infomation changer\n");
    printf("%i\n",argc);
    if (argc == 2) {
        if (strcmp(argv[1], "-blank") == 0) {
            printf("Blanking Now Playing\n");
            SendToMSN( "\\0Music\\00\\0{0} - {1}\\0\\0\\0\\0\\0\\0" );
        }
    } else if (argc == 4) {
        SendtoMsn("Music","{0} - {1}",argv[1], argv[2], argv[3]);
    } else if (argc == 6) {
        SendtoMsn(argv[1],argv[2],argv[3], argv[4], argv[5]);
    }  else if (argc == 3) {
        if (strcmp(argv[1], "-video") == 0) {
            SendtoMsn("Game","{0} - {1}",argv[2], "","");
        } else {
            SendtoMsn("Music","{0} - {1}",argv[1], argv[2], "");
        }
    }

}
