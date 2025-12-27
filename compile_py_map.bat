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

echo Done: %OUT_WAD%
endlocal
