@echo off
setlocal

rem Re-open under cmd /k so this visible owner console survives Explorer's cmd /c wrapper.
if not defined MYLES_PERSISTENT_CONSOLE (
  set "MYLES_PERSISTENT_CONSOLE=1"
  cmd /k call "%~f0"
  exit /b
)

title Myles - Local AI Console
set "MYLES_ROOT=%LOCALAPPDATA%\MylesAI"
set "MYLES_PY=%MYLES_ROOT%\.venv\Scripts\python.exe"
set "MYLES_PYW=%MYLES_ROOT%\.venv\Scripts\pythonw.exe"
set "MYLES_LOG=%MYLES_ROOT%\logs\start_latest.log"

if not exist "%MYLES_PY%" (
  echo Myles Python environment was not found:
  echo %MYLES_PY%
  echo.
  pause
  exit /b 1
)
if not exist "%MYLES_PYW%" set "MYLES_PYW=%MYLES_PY%"

if not exist "%MYLES_ROOT%\logs" mkdir "%MYLES_ROOT%\logs" >nul 2>&1
echo [%date% %time%] Starting hidden Myles supervisor > "%MYLES_LOG%"
start "Myles Supervisor" /b "%MYLES_PYW%" "%MYLES_ROOT%\runtime_supervisor.py" >> "%MYLES_LOG%" 2>&1
set "MYLES_SUPERVISOR_STARTED=1"

echo.
echo ============================================================
echo  MYLES - LOCAL AI CONSOLE
echo ============================================================
echo  Core and workers run hidden. This is the single owner console.
echo  Logs: %MYLES_ROOT%\logs
echo.
"%MYLES_PY%" "%MYLES_ROOT%\myles_console.py"
set "MYLES_EXIT=%ERRORLEVEL%"
echo.
if not "%MYLES_EXIT%"=="0" echo Console exited with code %MYLES_EXIT%. See the log above.
echo The hidden supervisor remains separate from this console.
echo Close this window only when you are done with the visible console.
pause
endlocal
