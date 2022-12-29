@echo off
IF "%INCLUDE%"=="" (
  "e:\Programs\VisualStudio14.0\VC\vcvarsall.bat" x86_amd64
  )

SET MODE=%1
IF "%MODE%"=="" (set MODE=msvc)
IF "%MODE%"=="clang" ( GOTO clang)
IF "%MODE%"=="msvc" ( GOTO msvc )

echo Unknown option: %MODE%
GOTO end
:clang
echo Building with Clang
set CLANG_PATH=C:\ProgramData\Programs\Clang380\bin
%CLANG_PATH%\clang++ -std=c++14 -Wall -Wextra -Wignored-attributes -fms-compatibility-version=19 -fcxx-exceptions  -c -o build\shell\Debug\buddy_clang.o buddy.cpp

GOTO end

:msvc

cl /nologo /EHsc /Zi buddy.cpp /Fobuild\shell\Debug\buddy.obj /Febuild\shell\Debug\buddy.exe
IF "%ERRORLEVEL%"=="0" (
  build\shell\Debug\buddy.exe
)

:end


