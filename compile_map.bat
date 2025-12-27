@echo off
setlocal

if not exist "build" (
  mkdir "build"
)

java -cp tools\wadc.jar org.redmars.wadc.WadCCLI -o build\hostel.wad src\scripts\hostel_layout.wl

endlocal
