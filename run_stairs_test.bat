@echo off
setlocal

set "DOOM_EXE=C:\Games\Windows-UZDoom-4.14.3\uzdoom.exe"
set "IWAD=C:\Games\Windows-UZDoom-4.14.3\DOOM2.WAD"
set "PWAD=build\py_stairs_test.wad"

if not exist "%DOOM_EXE%" (
    echo Error: Doom executable not found at:
    echo "%DOOM_EXE%"
    echo Please verify the path in run_stairs_test.bat
    pause
    exit /b 1
)

if not exist "%IWAD%" (
    echo Error: Doom 2 IWAD not found at:
    echo "%IWAD%"
    echo Please verify the path in run_stairs_test.bat
    pause
    exit /b 1
)

echo Launching stairs test...
call .\compile_py_stairs_test.bat
if errorlevel 1 exit /b 1
"%DOOM_EXE%" -iwad "%IWAD%" -file "%PWAD%" -warp 1

endlocal
