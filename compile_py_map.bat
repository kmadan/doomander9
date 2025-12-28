@echo off
setlocal

set "PY=py -3"
set "ZDBSP=C:\Games\Ultimate Doom Builder\Compilers\Nodebuilders\zdbsp.exe"

set "RAW_WAD=build\py_hostel_full_raw.wad"
set "OUT_WAD=build\py_hostel_full.wad"

if not exist "build" mkdir "build"

echo Generating UDMF WAD (raw)...
%PY% src\python_generator\main_hostel.py
if errorlevel 1 exit /b 1

if not exist "%ZDBSP%" (
  echo Error: zdbsp not found at:
  echo "%ZDBSP%"
  exit /b 1
)

if not exist "%RAW_WAD%" (
  echo Error: raw WAD not found:
  echo "%RAW_WAD%"
  exit /b 1
)

echo Building nodes with zdbsp (UDMF)...
"%ZDBSP%" -c -X -o"%OUT_WAD%" "%RAW_WAD%"
if errorlevel 1 exit /b 1

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

echo Done: %OUT_WAD%
endlocal
