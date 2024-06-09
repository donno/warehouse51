@echo off
IF "%VCToolsInstallDir%"=="" (
  echo Run vcvarsall.bat a.k.a 'x64 Native Tools Command prompt' from Visual Studio
  goto END
)

SET PDFIUM_DOWNLOAD="https://github.com/bblanchon/pdfium-binaries/releases/download/chromium%%2F6517/pdfium-win-x64.tgz"
SET SDL2_DOWNLOAD="https://github.com/libsdl-org/SDL/releases/download/release-2.30.3/SDL2-devel-2.30.3-VC.zip"

REM Create build directory if it it doesn't exist.
IF NOT EXIST build\NUL mkdir build
IF NOT EXIST build\bin\NUL mkdir build\bin
IF NOT EXIST build\obj\NUL mkdir build\obj
IF NOT EXIST build\third\NUL mkdir build\third

REM Download and extract third party packages for Windows built with MSVC.
IF NOT EXIST build\pdfium-win-x64.tgz curl.exe %PDFIUM_DOWNLOAD% --output build\pdfium-win-x64.tgz --location
IF NOT EXIST build\SDL2-devel-2.30.3-VC.zip curl.exe %SDL2_DOWNLOAD% --output build\SDL2-devel-2.30.3-VC.zip --location
IF NOT EXIST third\include\fpdf_doc.h tar xf build\pdfium-win-x64.tgz -C build\third
IF NOT EXIST third\include\SDL.h tar xf build\SDL2-devel-2.30.3-VC.zip --strip-components=1 -C build\third

IF NOT EXIST build\bin\SDL2.dll copy build\third\lib\x64\SDL2.dll build\bin
IF NOT EXIST build\bin\pdfium.dll copy build\third\bin\pdfium.dll build\bin

REM The next part is where I would prefer to use Ninja.
cl /nologo /c /EHsc /Zi pdfium.cpp /Ibuild\third\include /Fobuild\obj\pdfium.obj
cl /nologo /c /EHsc /Zi pdf_view.cpp /Ibuild\third\include /Fobuild\obj\pdf_view.obj
cl /nologo /c /EHsc /Zi pdf_view_sdl2.cpp /Ibuild\third\include /Fobuild\obj\pdf_view_sdl2.obj

link /nologo build\obj\pdf_view.obj build\obj\pdfium.obj build\third\lib\pdfium.dll.lib /out:build\bin\pdf_view.exe
link /nologo build\obj\pdf_view_sdl2.obj build\obj\pdfium.obj build\third\lib\pdfium.dll.lib build\third\lib\x64\SDL2.lib /out:build\bin\pdf_view_sdl2.exe

:END

