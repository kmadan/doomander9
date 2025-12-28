@echo off
setlocal

if not exist "build" (
  mkdir "build"
)

java -cp tools\wadc.jar org.redmars.wadc.WadCCLI -o build\hostel.wad src\scripts\hostel_layout.wl

echo Building defs PK3 (DECORATE/MAPINFO)...
set "DEFS_STAGE=build\_defs_pk3"
set "DEFS_PK3=build\hostel_defs.pk3"

if exist "%DEFS_STAGE%" rmdir /S /Q "%DEFS_STAGE%"
mkdir "%DEFS_STAGE%"
mkdir "%DEFS_STAGE%\decorate"
mkdir "%DEFS_STAGE%\mapinfo"

copy /Y "src\decorate\decorate.txt" "%DEFS_STAGE%\decorate.txt" >nul
copy /Y "src\decorate\player.txt" "%DEFS_STAGE%\decorate\player.txt" >nul
copy /Y "src\mapinfo.txt" "%DEFS_STAGE%\mapinfo.txt" >nul
copy /Y "src\mapinfo\mapinfo.txt" "%DEFS_STAGE%\mapinfo\mapinfo.txt" >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%DEFS_STAGE%\*' -DestinationPath '%DEFS_PK3%' -Force" >nul
if errorlevel 1 (
  echo Error: failed to create %DEFS_PK3%
  exit /b 1
)

endlocal
