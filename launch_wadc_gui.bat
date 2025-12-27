@echo off
setlocal

REM Launch the WadC GUI (tools\wadc.jar)
set "WADC_JAR=%~dp0tools\wadc.jar"

if not exist "%WADC_JAR%" goto :ERR_NO_JAR

REM Start in the repo root so relative paths (examples/scripts) are easy to open.
pushd "%~dp0"

REM Prefer javaw so we don't keep a console window open.
%SystemRoot%\System32\where.exe javaw >nul 2>nul
if errorlevel 1 goto :ERR_NO_JAVAW

start "WadC GUI" /D "%~dp0" javaw -jar "%WADC_JAR%"

popd
endlocal

exit /b 0

:ERR_NO_JAR
echo Error: WadC jar not found:
echo "%WADC_JAR%"
echo.
echo Expected it at tools\wadc.jar
pause
exit /b 1

:ERR_NO_JAVAW
echo Error: javaw not found on PATH.
echo Install a JRE/JDK Java 8+ and ensure it is on PATH.
pause
popd
exit /b 1
