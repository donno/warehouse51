/**
    pcmd - pseudo command processor

    Designed for Windows as a way to execute commands with the intention of
    providing a rich text environment to provide easier copying/pasting and
    command execution. As well as provide a harness for additional commands
    to be implemented.

    A project by Sean Donnellan <darkdonno@gmail.com>

    Started February 2010.
*/

#include <windows.h>
#include <stdio.h>

#define VERSION_PCMD "0.0.1"
#define BUFSIZE 256

STARTUPINFO si;
PROCESS_INFORMATION pi;
SECURITY_ATTRIBUTES saAttr;

char chBuf[BUFSIZE];
void execv(int argc, char *argv[]) {
    HANDLE hStdOut;
    HANDLE hStdIn;
    HANDLE hStdOutChildWriter, hStdOutChildReader;
    HANDLE hStdInChildWriter, hStdInChildReader;
    DWORD dwRead;
    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
    saAttr.bInheritHandle = TRUE;
    saAttr.lpSecurityDescriptor = NULL;

    hStdOut = GetStdHandle(STD_OUTPUT_HANDLE);

    if (!CreatePipe(&hStdOutChildReader, &hStdOutChildWriter, &saAttr, 0)) {
        fprintf(stderr, "execv failed to pipe stdout (%d)\n", GetLastError());
    }

    //SetHandleInformation( hStdOutChildReader, HANDLE_FLAG_INHERIT, 0);

    if (!CreatePipe(&hStdInChildReader, &hStdInChildWriter, &saAttr, 0)) {
        fprintf(stderr, "execv failed to pipe stdin (%d)\n", GetLastError());
    }

    //SetHandleInfomation( hStdInChildWriter, HANDLE_FLAG_INHERIT, 0);

    ZeroMemory(&si, sizeof(STARTUPINFO));
    ZeroMemory(&pi, sizeof(PROCESS_INFORMATION));
    si.cb = sizeof(STARTUPINFO);
    si.hStdOutput = hStdOutChildWriter;
    si.hStdInput = hStdInChildReader;
    si.dwFlags |= STARTF_USESTDHANDLES;

    puts("============");
    if (!CreateProcess("C:\\Data\\Console\\grep.exe","grep.exe", NULL, NULL,TRUE, 0,NULL,NULL,&si, &pi)) {
        fprintf(stderr, "execv failed (%d)\n", GetLastError());
        return;
    }

    // Read
    // Write

    for (;;) {
        if (!ReadFile(hStdOutChildReader, chBuf, BUFSIZE, &dwRead, NULL) || dwRead ==0) break;
        printf("READ: [%s]\n", chBuf);
    }
    puts("============");
}

int main(int argc, char *argv[]) {
    puts("pcmd - psuedo command processor - " VERSION_PCMD);
    execv(1, argv);
    return 0;
}
