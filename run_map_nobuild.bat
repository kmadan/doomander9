@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

set "DOOM_EXE=C:\Games\Windows-UZDoom-4.14.3\uzdoom.exe"
set "IWAD=C:\Games\Windows-UZDoom-4.14.3\DOOM2.WAD"
set "PWAD=%SCRIPT_DIR%build\py_hostel_full.wad"
set "DEFS_PK3=%SCRIPT_DIR%build\hostel_defs.pk3"

REM Workaround: some systems show black/dark flashes with the Vulkan backend.
REM Force OpenGL. (If unsupported, it is ignored and the engine still launches.)
set "VIDEO_ARGS=+vid_preferbackend 0"

if not exist "%DOOM_EXE%" (
    echo Error: Doom executable not found at:
    echo "%DOOM_EXE%"
    pause
    exit /b 1
)

if not exist "%IWAD%" (
    echo Error: Doom 2 IWAD not found at:
    echo "%IWAD%"
    pause
    exit /b 1
)

if not exist "%PWAD%" (
    echo Error: PWAD not found at:
    echo "%PWAD%"
    echo Run compile_py_map.bat first.
    pause
    exit /b 1
)

if not exist "%DEFS_PK3%" (
    echo Error: defs PK3 not found at:
    echo "%DEFS_PK3%"
    echo Run compile_py_map.bat or compile_map.bat first.
    pause
    exit /b 1
)

echo Launching map (no build)...
start "UZDoom" "%DOOM_EXE%" -iwad "%IWAD%" -file "%PWAD%" "%DEFS_PK3%" -warp 1 %VIDEO_ARGS%

endlocal
