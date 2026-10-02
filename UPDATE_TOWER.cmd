@echo off
setlocal
title MYLES Tower Update
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0UPDATE_TOWER.ps1"
if errorlevel 1 (
  echo.
  echo MYLES update reported an error.
  pause
)
endlocal
