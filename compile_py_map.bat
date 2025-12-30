@echo off
setlocal

set "PY=py -3"
set "ZDBSP=C:\Games\Ultimate Doom Builder\Compilers\Nodebuilders\zdbsp.exe"
set "ACC="
set "ACS_INC="

set "RAW_WAD=build\py_hostel_full_raw.wad"
set "OUT_WAD=build\py_hostel_full.wad"

if not exist "build" mkdir "build"

REM Optional fast-fail ACS compile (runs before the slow Python map build).
REM Set SKIP_ACS=1 to skip.
if "%SKIP_ACS%"=="1" goto :AFTER_EARLY_ACS

REM If your UDB ships acc.exe under Compilers\ZDoom, prefer that.
set "EARLY_ACC=C:\Games\Ultimate Doom Builder\Compilers\ZDoom\acc.exe"
set "EARLY_ACS_INC=C:\Games\Ultimate Doom Builder\Compilers\ACS"
if exist "%EARLY_ACC%" (
  echo Pre-compiling ACS - intro text...
  "%EARLY_ACC%" -i "%EARLY_ACS_INC%" "src\acs\h9_intro.acs" "build\_acs_intro_test.o"
  if errorlevel 1 (
    echo Error: ACS compile failed - fast check
    exit /b 1
  )
)
:AFTER_EARLY_ACS

echo Generating UDMF WAD (raw)...
%PY% src\python_generator\main_hostel.py
if errorlevel 1 exit /b 1

if not exist "%ZDBSP%" (
  echo Error: zdbsp not found at:
  echo "%ZDBSP%"
  exit /b 1
)

REM Try to locate ACC relative to the configured ZDBSP path.
REM UDB layout is typically: Compilers\Nodebuilders\zdbsp.exe and Compilers\ACS\acc.exe
for %%I in ("%ZDBSP%") do set "UDB_COMPILERS_DIR=%%~dpI.."

REM Candidate locations (UDB ships acc.exe in either ACS or ZDoom depending on setup)
set "ACC=%UDB_COMPILERS_DIR%\ACS\acc.exe"
if not exist "%ACC%" set "ACC=%UDB_COMPILERS_DIR%\ZDoom\acc.exe"
if not exist "%ACC%" set "ACC=%UDB_COMPILERS_DIR%\zdoom\acc.exe"

REM zcommon.acs is typically in Compilers\ACS.
set "ACS_INC=%UDB_COMPILERS_DIR%\ACS"

REM Fallback: find acc.exe in PATH.
if not exist "%ACC%" (
  for /f "delims=" %%P in ('where acc.exe 2^>nul') do (
    set "ACC=%%P"
    goto :ACC_FOUND
  )
)
:ACC_FOUND
if exist "%ACC%" (
  REM If the ACS include folder isn't present, fall back to the acc.exe folder.
  if not exist "%ACS_INC%" (
    for %%I in ("%ACC%") do set "ACS_INC=%%~dpI"
  )
)

REM Prefer the explicitly-known UDB toolchain when present (matches the early ACS compile step).
if exist "%EARLY_ACC%" (
  set "ACC=%EARLY_ACC%"
  set "ACS_INC=%EARLY_ACS_INC%"
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
mkdir "%DEFS_STAGE%\acs"

copy /Y "src\decorate\decorate.txt" "%DEFS_STAGE%\decorate.txt" >nul
copy /Y "src\decorate\player.txt" "%DEFS_STAGE%\decorate\player.txt" >nul
copy /Y "src\mapinfo.txt" "%DEFS_STAGE%\mapinfo.txt" >nul
copy /Y "src\mapinfo\mapinfo.txt" "%DEFS_STAGE%\mapinfo\mapinfo.txt" >nul
copy /Y "src\acs\h9_intro.acs" "%DEFS_STAGE%\acs\h9_intro.acs" >nul

echo Compiling ACS (intro text)...
if exist "%ACC%" (
  echo Using ACC: "%ACC%"
  "%ACC%" -i "%ACS_INC%" "src\acs\h9_intro.acs" "%DEFS_STAGE%\acs\h9_intro.o"
  if errorlevel 1 (
    echo Error: ACS compile failed
    exit /b 1
  )
) else (
  echo Warning: acc.exe not found.
  echo - Checked relative to ZDBSP: %UDB_COMPILERS_DIR%\ACS\acc.exe
  echo - Checked PATH via: where acc.exe
  echo Skipping ACS compilation; intro text will not appear.
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%DEFS_STAGE%\*' -DestinationPath '%DEFS_PK3%' -Force" >nul
if errorlevel 1 (
  echo Error: failed to create %DEFS_PK3%
  exit /b 1
)

echo Done: %OUT_WAD%
endlocal
