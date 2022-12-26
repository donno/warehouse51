#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>
//#include <sys/wait.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <limits.h>

#define BUFSIZE 1024

#define MAX_ARGS 32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tchar.h>


int parse_command(char *line, char **argv, int max) {
  int len = strlen(line);
  int pos;
  int argc = 0;
  int start = 0;

  /* Scan through the input to extract space-separated tokens */
  for (pos = 0; pos <= len; pos++) {
    if (('\n' == line[pos]) || (' ' == line[pos]) || (pos == len)) {
      /* We found a token; add it to the argv array */
      line[pos] = '\0';
      if ((pos > start) && (argc+1 < max))
        argv[argc++] = &line[start];
      start = pos+1;
    }
  }

  return argc;
}

void run_program(const char *filename, TCHAR **argv) {
    STARTUPINFO si;
    PROCESS_INFORMATION pi;

    ZeroMemory( &si, sizeof(si) );
    si.cb = sizeof(si);
    ZeroMemory( &pi, sizeof(pi) );

  /* Fork off a child process */
    
 if( !CreateProcess( NULL,   // No module name (use command line)
        filename,           // Command line
        NULL,           // Process handle not inheritable
        NULL,           // Thread handle not inheritable
        FALSE,          // Set handle inheritance to FALSE
        0,              // No creation flags
        NULL,           // Use parent's environment block
        NULL,           // Use parent's starting directory 
        &si,            // Pointer to STARTUPINFO structure
        &pi )           // Pointer to PROCESS_INFORMATION structure
    ) 
    {
        printf( "CreateProcess failed (%d).\n", GetLastError() );
        return;
    }

    
  /*pid_t pid = fork();
  if (0 > pid) {
    perror("fork");
    return;
  }
  else if (0 == pid) {*.
    /* in child process */
    /*execvp(filename,argv);
    perror("execvp");
    exit(1);
  } else {*/
    /* in parent process */
    /*if (0 > waitpid(pid,NULL,0))
      perror("waitpid");
  }*/
}

void process_line(char *line, int *done)
{
  char *argv[MAX_ARGS+1];

  /* Extract the space-separated tokens from the command line */
  int argc = parse_command(line,argv,MAX_ARGS);
  argv[argc] = NULL; /* so we can pass it to execve() */

  if (0 == argc)
    return;

  /* Check which command was requested and take appropriate action */
  if (!strcmp(argv[0],"cd")) {
    /* Change directory */
    if (2 > argc)
      printf("Usage: cd <path>\n");
    else if (0 > chdir(argv[1]))
      perror(argv[1]);
  }
  else if (!strcmp(argv[0],"pwd")) {
    /* Print current working directory */
    char path[PATH_MAX];
    if (NULL == getcwd(path,PATH_MAX))
      perror("getcwd");
    else
      printf("%s\n",path);
  }
  else if (!strcmp(argv[0],"exit")) {
    /* Exit shell */
    *done = 1;
  }
  else {
    /* Run a program */
    run_program(argv[0],argv);
    return;
  }
}

int main(int argc, TCHAR *argv[]) {
  char input[2*BUFSIZE+1];
  int pos = 0;
  int linestart = 0;
  setbuf(stdout,NULL);
  if (isatty(STDIN_FILENO))
    printf("$ ");
  int r;
  int done = 0;

  /* Read some text from standard input */
  while (!done && (0 < (r = read(0,&input[pos],BUFSIZE)))) {
    input[pos+r] = '\0';
    int end = pos+r;

    /* Scan through the input data to find \n characters, indicating
       end-of-line. For each complete line, we call the process_line function
       to extract the command name and arguments */
    while (pos < end) {
      if ('\n' == input[pos]) {
        input[pos] = '\0';
        process_line(&input[linestart],&done);
        if (isatty(STDIN_FILENO))
          printf("$ ");
        linestart = pos+1;
      }
      pos++;
    }

    /* If there's any remaining data in the buffer that does not yet constitute
       a complete line, then keep it, but shift it up to the beginning of the
       buffer. Data read on the next iteration will be placed after this. */
    memmove(&input[0],&input[linestart],pos-linestart);
    pos -= linestart;
    linestart = 0;

    /* Since we have a fixed size buffer, ignore any lines that won't fit */
    if (pos >= BUFSIZE) {
      printf("Line too long; ignored");
      pos = 0;
    }
  }
  if (0 > r)
    perror("read");

  return 0;
}
