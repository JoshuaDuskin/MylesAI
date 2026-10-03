[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Data = Join-Path $Root "data"
$Logs = Join-Path $Root "logs"
$Supervisor = Join-Path $Root "bin\runtime_supervisor_v074.py"
$PythonW = Join-Path $Root ".venv\Scripts\pythonw.exe"
$PidFile = Join-Path $Data "runtime_supervisor_v074.pid"
$LockFile = Join-Path $Data "runtime_supervisor_v074.lock"
$StateFile = Join-Path $Data "runtime_guardian_state.json"
$LogFile = Join-Path $Logs "runtime_guardian.log"

New-Item -ItemType Directory -Force -Path $Data, $Logs | Out-Null

function Write-GuardianLog([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
}

function Get-SupervisorRows {
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessId -ne $PID -and ([string]$_.CommandLine) -match "(?i)runtime_supervisor_v074\.py"
    })
}

function Test-LocalRuntime {
    $core = $false
    $bridge = $false
    $gateway = $false
    try { $core = $null -ne (Invoke-RestMethod "http://127.0.0.1:8766/health" -TimeoutSec 4) } catch {}
    try { $bridge = @(Get-NetTCPConnection -State Listen -LocalPort 8790 -ErrorAction SilentlyContinue).Count -gt 0 } catch {}
    try { $gateway = @(Get-NetTCPConnection -State Listen -LocalPort 8791 -ErrorAction SilentlyContinue).Count -gt 0 } catch {}
    return ($core -and $bridge -and $gateway)
}

function Read-FailureCount {
    try {
        $state = Get-Content $StateFile -Raw -ErrorAction Stop | ConvertFrom-Json
        return [int]$state.consecutive_failures
    } catch {
        return 0
    }
}

function Save-FailureCount([int]$Count) {
    [ordered]@{
        consecutive_failures = $Count
        checked_at = [DateTimeOffset]::UtcNow.ToString("o")
    } | ConvertTo-Json | Set-Content $StateFile -Encoding UTF8
}

if (-not (Test-Path $Supervisor -PathType Leaf)) {
    Write-GuardianLog "Supervisor source is missing: $Supervisor"
    exit 2
}
if (-not (Test-Path $PythonW -PathType Leaf)) {
    $PythonW = Join-Path $Root ".venv\Scripts\python.exe"
}
if (-not (Test-Path $PythonW -PathType Leaf)) {
    Write-GuardianLog "Python runtime is missing under $Root\.venv"
    exit 3
}

$rows = @(Get-SupervisorRows)
if ($rows.Count -eq 0) {
    Remove-Item $PidFile, $LockFile -Force -ErrorAction SilentlyContinue
    $started = Start-Process -FilePath $PythonW -ArgumentList $Supervisor -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    Write-GuardianLog ("Supervisor was absent; started launcher PID " + $started.Id)
    Save-FailureCount 0
    exit 0
}

if (Test-LocalRuntime) {
    Save-FailureCount 0
    exit 0
}

$failures = (Read-FailureCount) + 1
Save-FailureCount $failures
Write-GuardianLog "Supervisor exists but core/bridge/gateway health is incomplete (failure $failures of 3)"
if ($failures -lt 3) {
    exit 1
}

# Three consecutive five-minute checks failed. Drain only logical supervisor
# roots; /T lets Windows include the uv-backed Python child without mistaking it
# for a second logical owner.
$ids = @($rows | ForEach-Object { [int]$_.ProcessId })
$roots = @($rows | Where-Object { $ids -notcontains [int]$_.ParentProcessId })
foreach ($row in $roots) {
    try {
        Start-Process -FilePath "taskkill.exe" -ArgumentList @("/PID", [string]$row.ProcessId, "/T", "/F") -WindowStyle Hidden -Wait | Out-Null
        Write-GuardianLog ("Drained unhealthy supervisor tree PID " + $row.ProcessId)
    } catch {
        Write-GuardianLog ("Could not drain unhealthy supervisor tree PID " + $row.ProcessId + ": " + $_.Exception.Message)
    }
}
Start-Sleep -Seconds 2
if (@(Get-SupervisorRows).Count -eq 0) {
    Remove-Item $PidFile, $LockFile -Force -ErrorAction SilentlyContinue
}
$started = Start-Process -FilePath $PythonW -ArgumentList $Supervisor -WorkingDirectory $Root -WindowStyle Hidden -PassThru
Write-GuardianLog ("Started recovered canonical supervisor launcher PID " + $started.Id)
Save-FailureCount 0
exit 0
