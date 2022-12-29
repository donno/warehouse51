
#define UNICODE 1
#include <windows.h>
#include <stdio.h>

struct S_Login
{
  //TCHAR username[255];
  //TCHAR password[255];
  //TCHAR domain[255];

} login;

LPCWSTR login_username = L"xbmc";
LPCWSTR login_password = L"xbmc";


LPCWSTR applicationPath = L"c:\\Windows\\notepad.exe";
TCHAR commandLine[1024];


void DisplayError(LPWSTR pszAPI)
{
    LPVOID lpvMessageBuffer;

    DWORD lastError = GetLastError();

    FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER |
        FORMAT_MESSAGE_FROM_SYSTEM,
        NULL, lastError,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPWSTR)&lpvMessageBuffer, 0, NULL);

    //
    //... now display this string
    //
    wprintf(L"ERROR: API        = %s.\n", pszAPI);
    wprintf(L"       error code = %08x.\n", lastError);
    wprintf(L"       message    = %s.\n", (LPWSTR)lpvMessageBuffer);

    //
    // Free the buffer allocated by the system
    //
    LocalFree(lpvMessageBuffer);

    ExitProcess(GetLastError());
}

#include <Userenv.h>

int main()
{
  //strcpy(login.username, "
  commandLine[0] = '\0';

  PROCESS_INFORMATION processInformation = {0};
  STARTUPINFO startupInformation = {0};
  startupInformation.cb = sizeof(STARTUPINFO);
  HANDLE    loginToken;
  LPVOID    enviromentBlock;
  WCHAR               szUserProfile[256] = L"";

  if (!LogonUser(login_username, NULL, login_password, LOGON32_LOGON_INTERACTIVE,
          LOGON32_PROVIDER_DEFAULT, &loginToken))
      DisplayError(L"LogonUser");

  // Gets the enviroment block for the given user associated with the provided
  // login token.
  if (!CreateEnvironmentBlock(&enviromentBlock, loginToken, TRUE))
      DisplayError(L"CreateEnvironmentBlock");

  DWORD     dwSize;
  dwSize = sizeof(szUserProfile)/sizeof(WCHAR);

  // :TODO: Consider looking up the user's profile directory and using that
  // as the current working directory (GetUserProfileDirectory).

  CreateProcessWithLogonW(
    login_username,       // Username
    NULL, //login.domain, // Domain
    login_password,       // Password
    LOGON_WITH_PROFILE,   // Logon flags.
    applicationPath,      // Application name.
    commandLine,          // Command line
    CREATE_UNICODE_ENVIRONMENT, // Creation flags.
    enviromentBlock,      // The enviroment block
    L"C:\\windows\\", //The CWD has the same current drive and directory as this process.
    &startupInformation,
    &processInformation);

  DisplayError(L"FOO");

  //DestroyEnvironmentBlock
  return 0;
}