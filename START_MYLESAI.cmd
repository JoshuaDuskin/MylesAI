@echo off
setlocal
title Myles - Local AI Console

set "MYLES_ROOT=%LOCALAPPDATA%\MylesAI"
set "MYLES_PY=%MYLES_ROOT%\.venv\Scripts\python.exe"
set "MYLES_PYW=%MYLES_ROOT%\.venv\Scripts\pythonw.exe"
set "MYLES_SUPERVISOR=%MYLES_ROOT%\bin\runtime_supervisor_v074.py"
set "MYLES_CONSOLE=%MYLES_ROOT%\bin\myles_console_v074.py"
set "MYLES_LOG=%MYLES_ROOT%\logs\start_latest.log"

if not exist "%MYLES_PY%" (
  echo.
  echo MYLES Python environment was not found:
  echo %MYLES_PY%
  echo.
  pause
  exit /b 1
)
if not exist "%MYLES_PYW%" set "MYLES_PYW=%MYLES_PY%"
if not exist "%MYLES_SUPERVISOR%" (
  echo.
  echo MYLES canonical supervisor is missing:
  echo %MYLES_SUPERVISOR%
  echo.
  pause
  exit /b 1
)
if not exist "%MYLES_CONSOLE%" (
  echo.
  echo MYLES canonical console is missing:
  echo %MYLES_CONSOLE%
  echo.
  pause
  exit /b 1
)

if not exist "%MYLES_ROOT%\logs" mkdir "%MYLES_ROOT%\logs" >nul 2>&1

set "MYLES_SUPERVISOR_RUNNING="
if exist "%MYLES_ROOT%\data\runtime_supervisor_v074.pid" (
  for /f "usebackq delims=" %%P in ("%MYLES_ROOT%\data\runtime_supervisor_v074.pid") do (
    tasklist /FI "PID eq %%P" /NH 2>nul | findstr /C:"%%P" >nul
    if not errorlevel 1 set "MYLES_SUPERVISOR_RUNNING=1"
  )
)

if defined MYLES_SUPERVISOR_RUNNING (
  echo [%date% %time%] Reusing canonical MYLES supervisor > "%MYLES_LOG%"
  set "MYLES_SUPERVISOR_STARTED=0"
) else (
  echo [%date% %time%] Starting canonical hidden MYLES supervisor > "%MYLES_LOG%"
  start "" /b "%MYLES_PYW%" "%MYLES_SUPERVISOR%" >> "%MYLES_LOG%" 2>&1
  set "MYLES_SUPERVISOR_STARTED=1"
)

echo.
echo ============================================================
echo  MYLES - LOCAL AI CONSOLE
echo ============================================================
echo  One visible console. Workers stay hidden.
echo  Canonical repo: JoshuaDuskin/MylesAI
echo  Logs: %MYLES_ROOT%\logs
echo.

"%MYLES_PY%" "%MYLES_CONSOLE%"
set "MYLES_EXIT=%ERRORLEVEL%"

echo.
if not "%MYLES_EXIT%"=="0" echo Console exited with code %MYLES_EXIT%.
echo Closing this window does not stop the hidden MYLES runtime.
pause
endlocal
