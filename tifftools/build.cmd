@echo off
REM Simple build script for using in the native tools command prompt for VS2022.

SET VCPKG_PATH=D:\vcs\vcpkg\installed\x64-windows-static

IF NOT EXIST build\NUL mkdir build

cl /nologo /Zi /std:c++17 /EHsc /O2 /c TiffTools.cpp /I%VCPKG_PATH%\include /Fo:build\TiffTools.obj
cl /nologo /Zi /std:c++17 /EHsc /O2 /c tiff_to_xyz.cpp /I%VCPKG_PATH%\include /Fo:build\tiff_to_xyz.obj

link /nologo build\tiff_to_xyz.obj build\TiffTools.obj ^
    %VCPKG_PATH%\lib\tiff.lib ^
    %VCPKG_PATH%\lib\lzma.lib ^
    %VCPKG_PATH%\lib\zlib.lib ^
    %VCPKG_PATH%\lib\jpeg.lib ^
    %VCPKG_PATH%\lib\Lerc.lib ^
    %VCPKG_PATH%\lib\zstd.lib ^
    %VCPKG_PATH%\lib\deflatestatic.lib ^
    %VCPKG_PATH%\lib\libsharpyuv.lib ^
    %VCPKG_PATH%\lib\libwebp.lib ^
    /debug /PDB:build\tiff_to_xyz.pdb  ^
    /out:build\tiff_to_xyz.exe
