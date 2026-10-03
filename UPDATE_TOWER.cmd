@echo off
setlocal
title MYLES Tower Update
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0UPDATE_TOWER.ps1"
set "MYLES_EXIT=%ERRORLEVEL%"

echo.
echo ============================================================
if "%MYLES_EXIT%"=="0" (
  echo MYLES updater finished.
) else (
  echo MYLES updater reported exit code %MYLES_EXIT%.
)
echo.
echo Saved result:
echo C:\Users\Joshu\AppData\Local\MylesAI\logs\tower_update_RESULT.txt
echo Saved log:
echo C:\Users\Joshu\AppData\Local\MylesAI\logs\tower_update_latest.log
if exist "C:\Users\Joshu\AppData\Local\MylesAI\logs\tower_update_RESULT.txt" (
  echo.
  type "C:\Users\Joshu\AppData\Local\MylesAI\logs\tower_update_RESULT.txt"
)
echo ============================================================
echo.
echo This window will stay open so you can copy the result.
pause
endlocal
exit /b %MYLES_EXIT%
