// cl launchAs.v2.cpp Advapi32.lib Userenv.lib
#define UNICODE 1
#include <windows.h>

#include <Userenv.h>

#include <stdio.h>

static TCHAR login_username[18] = L"LAUNCHER_POSITION";
static TCHAR login_username[255] = L"USERNAME";
static TCHAR login_domain[255] = L"DOMAIN";
static TCHAR login_password[255] = L"PASSWORD";

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

void Replicate()
{
  
}
int main(int argc, char argv[0])
{
  commandLine[0] = '\0';

  PROCESS_INFORMATION processInformation = {0};
  STARTUPINFO startupInformation = {0};
  startupInformation.cb = sizeof(STARTUPINFO);
  HANDLE    loginToken;
  LPVOID    environmentBlock = NULL;
  WCHAR     szUserProfile[256] = L"";

  if (!LogonUser(login_username, NULL, login_password, LOGON32_LOGON_INTERACTIVE,
          LOGON32_PROVIDER_DEFAULT, &loginToken))
      DisplayError(L"LogonUser");

  // Gets the enviroment block for the given user associated with the provided
  // login token.
  //if (!CreateEnvironmentBlock(&environmentBlock, loginToken, TRUE))
  //    DisplayError(L"CreateEnvironmentBlock");
  // Creation flag should be CREATE_UNICODE_ENVIRONMENT below.

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
    environmentBlock,      // The environment block
    L"C:\\windows\\", //The CWD has the same current drive and directory as this process.
    &startupInformation,
    &processInformation);

  DisplayError(L"Launch");

  CloseHandle(loginToken);
  CloseHandle(processInformation.hProcess);
  CloseHandle(processInformation.hThread);

  //DestroyEnvironmentBlock(&environmentBlock);
  return 0;
}