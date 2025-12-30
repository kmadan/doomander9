@echo off
setlocal

set "ACC=C:\Games\Ultimate Doom Builder\Compilers\ZDoom\acc.exe"
set "ACS_INC=C:\Games\Ultimate Doom Builder\Compilers\ACS"

set "SRC=src\acs\h9_intro.acs"
set "OUT=build\_acs\h9_intro.o"

if not exist "build\_acs" mkdir "build\_acs"

if not exist "%ACC%" (
  echo Error: acc.exe not found at:
  echo "%ACC%"
  exit /b 1
)

if not exist "%SRC%" (
  echo Error: ACS source not found at:
  echo "%SRC%"
  exit /b 1
)

echo Compiling ACS intro...
"%ACC%" -i "%ACS_INC%" "%SRC%" "%OUT%"
if errorlevel 1 exit /b 1

echo OK: %OUT%
endlocal
