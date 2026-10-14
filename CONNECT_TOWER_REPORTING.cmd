@echo off
setlocal
set "MYLES_ROOT=%LOCALAPPDATA%\MylesAI"
if not exist "%MYLES_ROOT%\bin\tower_reporting_connect.py" (
  echo MYLES reporting connector is not installed on the tower.
  echo The canonical MylesAI automatic updater must install this release first.
  pause
  exit /b 2
)
if not exist "%MYLES_ROOT%\.venv\Scripts\python.exe" (
  echo MYLES Python runtime is unavailable. No changes made.
  pause
  exit /b 2
)
"%MYLES_ROOT%\.venv\Scripts\python.exe" "%MYLES_ROOT%\bin\tower_reporting_connect.py"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo Connection could not be verified. Credentials were not published.
pause
exit /b %RC%
