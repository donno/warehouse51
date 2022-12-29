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
 *  This is My (Donno's) First C++ Program
 *  // TODO: Make a GUI version
 *
 */

#include <iostream>
#include <Windows.h>
#include <string>

#define MSN_MAX_LENGTH 256
//typedef CCP const char *;

/*****************************************************************************
 * SendToMSN
 *****************************************************************************/
static void SendToMSN(char *psz_msg )
{
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
static void SendtoMsn(const char * type, const char * formatting, const char *info0,const char *info1,const char *info2)
{
    char psz_tmp[MSN_MAX_LENGTH];
    snprintf( psz_tmp,MSN_MAX_LENGTH,"\\0%s\\01\\0%s\\0%s\\0%s\\0%s\\0\\0\\0",type,formatting,info0,info1, info2);
    SendToMSN(psz_tmp);
}

/*****************************************************************************
 * SendtoMsn
 *****************************************************************************/
/*
static void SendtoMsn(const char *title,const char *artist,const char *album)
{
    /* By Default title,artist,album should be NULL 
    char psz_tmp[MSN_MAX_LENGTH];
    // ACCEPTABLE Types   Music   Office
    snprintf( psz_tmp,MSN_MAX_LENGTH,"\\0Music\\01\\0%s\\0%s\\0%s\\0%s\\0\\0\\0","{0} - {1}",title,artist, album);
    SendToMSN(psz_tmp);
}*/

static void AskInfo(const char * type, const char * formatting,const char * m1,const char * m2,const char * m3)
{
	// this is a little generic :)
    std::string var1, var2, var3;
    std::cout << m1;
    std::cin >> var1;
    std::cout << m2;
    std::cin >> var2;
    std::cout << m3;
    std::cin >> var3;
    const char *info0 = var1.c_str();
    const char *info1 = var2.c_str();
    const char *info2 = var3.c_str();
    SendtoMsn(type,formatting,info0,info1,info2);
}
/*
static void AskSongInfo()
{
    std::string name, artist, album;
    std::cout << "Enter Artist Name? ";
    std::cin >> artist;
    std::cout << "Enter Track Name? ";
    std::cin >> name;
    std::cout << "Enter Album Name? ";
    std::cin >> album;
    const char *ar= artist.c_str();
    const char *al= album.c_str();
    const char *tn= name.c_str();
    SendtoMsn("Music","{0} - {1}",tn,ar,al);
}

static void AskGameInfo()
{
    std::string name, pub, album;
    std::cout << "Enter Publisher/maker Name? ";
    std::cin >> pub;
    std::cout << "Enter Game Name? ";
    std::cin >> name;
    //std::cout << "Enter Album Name? ";
    //std::cin >> album;
    album = "";
    const char *ar= pub.c_str();
    const char *al= album.c_str();
    const char *tn= name.c_str();
    SendtoMsn("Games","{0} (By {1})",tn,ar,al);
}*/
int main(int argc, char **argv)
{
    char answerYN;
    std::cout << "Windows Live Messenger::Now Playing infomation changer" << std::endl;

    for (int i = 1; i < argc; i++)
    {
        if (0 == strcasecmp (argv[i], "-h"))
        {
            std::cout << "Usage Help" << std::endl;
            std::cout << " -h Brings up the help (this infomation)" << std::endl;
            std::cout << " [none] no arguments, brings up the interactive choices" << std::endl;
            std::cout << " else ";
            std::cout << argv[0];
            std::cout << " title artist album  (sets now playing based on passed arguments" << std::endl;
            return 0;
        }
    }
    if (argc == 2)
    {
        SendtoMsn("Music","{0} - {1}",argv[1],argv[2],NULL);
        return 0;
    }
    else  if (argc == 3)
    {
        SendtoMsn("Music","{0} - {1}",argv[1],argv[2],argv[3]);
        return 0;
    }
    std::cout << "Would you set Now Playing [Y] or clear Now Playing [N]?";
    std::cin >> answerYN;
    switch (answerYN)
    {
        case 'Y':
        case 'y':
            std::cout << "Setting Now Playing" << std::endl;
            std::cout << "Which type [M]usic, [G]ame or [O]ffice?";
            std::cin >> answerYN;
            switch (answerYN)
            {
                case 'M':
                case 'm':
                    AskInfo("Music","{0} - {1}","Enter Artist Name? ","Enter Track Name? ","Enter Album Name? ");
                    break;
                case 'G':
                case 'g':
                    AskInfo("Game","{0} ({1})","Enter Publisher Name? ","Enter Game Name? ","Enter Anything (not used)?");
                    break;
                case 'O':
                case 'o':
                    AskInfo("Office","{0}","Enter Anything (not used)?","Enter FIlename Name? ","Enter Anything (not used)?");
                    break;
                default:
                std::cout << "Invaild/Cancelled";
                break;
            }
        break;
        case 'N':
        case 'n':
        std::cout << "Blanking Now Playing" << std::endl;
        SendToMSN( "\\0Music\\00\\0{0} - {1}\\0\\0\\0\\0\\0\\0" );
        break;
        default:
        std::cout << "Enter Y or N next time";
        break;
    }
    return 0;
}
