@echo off
setlocal
title MYLES Last Tower Update Result
set "RESULT=%LOCALAPPDATA%\MylesAI\logs\tower_update_RESULT.txt"
set "LOG=%LOCALAPPDATA%\MylesAI\logs\tower_update_latest.log"

if exist "%RESULT%" (
  start "" notepad.exe "%RESULT%"
  echo Opened the last MYLES update result in Notepad:
  echo %RESULT%
  echo.
  echo This window will stay open.
  pause
  exit /b 0
)

echo The result file was not found:
echo %RESULT%
echo.
if exist "%LOG%" (
  echo Opening the updater log instead:
  echo %LOG%
  start "" notepad.exe "%LOG%"
) else (
  echo No updater result or updater log exists yet.
)
echo.
pause
exit /b 1
