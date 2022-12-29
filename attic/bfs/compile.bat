@echo off
cl /nologo /c /Zi /EHsc Map.cpp
cl /nologo /c /Zi /EHsc Position.cpp
cl /nologo /c /Zi /EHsc PathFinder.cpp
cl /nologo PathFinder.obj Map.obj Position.obj

rem Uncomment the following to skip linting
goto end

:lint
cpplint.py --filter=-whitespace/braces,-readability/streams Position.cpp
cpplint.py --filter=-whitespace/braces,-readability/streams Map.cpp
cpplint.py --filter=-whitespace/braces,-readability/streams PathFinder.cpp

:end