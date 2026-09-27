@echo off
setlocal
title Stop Myles safely
set "MYLES_ROOT=%LOCALAPPDATA%\MylesAI"
set "MYLES_PY=%MYLES_ROOT%\.venv\Scripts\python.exe"
if not exist "%MYLES_PY%" (
  echo Myles Python environment was not found.
  pause
  exit /b 1
)
"%MYLES_PY%" "%MYLES_ROOT%\runtime_supervisor.py" stop
if errorlevel 1 echo Stop request returned an error. Check %MYLES_ROOT%\logs\supervisor.log
echo Myles stop request completed. No process tree kill was used.
pause
endlocal
