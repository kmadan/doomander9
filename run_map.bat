@echo off
setlocal

set "DOOM_EXE=C:\Games\Windows-UZDoom-4.14.3\uzdoom.exe"
set "IWAD=C:\Games\Windows-UZDoom-4.14.3\DOOM2.WAD"
set "PWAD=build\py_hostel_test.wad"

if not exist "%DOOM_EXE%" (
    echo Error: Doom executable not found at:
    echo "%DOOM_EXE%"
    echo Please verify the path in run_map.bat
    pause
    exit /b 1
)

if not exist "%IWAD%" (
    echo Error: Doom 2 IWAD not found at:
    echo "%IWAD%"
    echo Please verify the path in run_map.bat
    pause
    exit /b 1
)

echo Launching map...
"%DOOM_EXE%" -iwad "%IWAD%" -file "%PWAD%" -warp 1

endlocal
