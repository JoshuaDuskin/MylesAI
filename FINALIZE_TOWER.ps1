[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    $ea = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$PSCommandPath)
    Start-Process powershell.exe -ArgumentList $ea -Verb RunAs | Out-Null
    exit
}

$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Recovery = Join-Path $env:LOCALAPPDATA ("MylesAI_Finalize_" + $Stamp)
New-Item -ItemType Directory -Force -Path $Recovery | Out-Null

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Write-Host $line
    Add-Content -Path (Join-Path $Recovery "finalize.log") -Value $line
}

if (-not (Test-Path (Join-Path $Root ".git"))) { throw "MYLES repo not found at $Root" }
$Git = (Get-Command git.exe -ErrorAction Stop).Source

function Git {
    param([string[]]$A)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $o = & $Git -C $Root @A 2>&1
        $c = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
    if ($c -ne 0) { throw ("git " + ($A -join " ") + " failed: " + (($o | Out-String).Trim())) }
    return @($o | ForEach-Object { [string]$_ })
}

Log "============================================================"
Log "MYLES FINAL CANONICAL CLEANUP"
Log "============================================================"

# Preserve status before touching anything.
$before = @(Git @("status","--short","--branch"))
$before | Set-Content (Join-Path $Recovery "git_status_before.txt")

# Pull the latest canonical source.
Git @("remote","set-url","origin","https://github.com/JoshuaDuskin/MylesAI.git") | Out-Null
Git @("fetch","origin","main","--prune") | Out-Null
Git @("checkout","-B","main","origin/main","--force") | Out-Null
Git @("reset","--hard","origin/main") | Out-Null
Log "PASS: source reset to canonical MylesAI/main"

# Keep genuinely local, untracked files local without deleting them.
$exclude = Join-Path $Root ".git\info\exclude"
New-Item -ItemType Directory -Force -Path (Split-Path $exclude -Parent) | Out-Null
if (-not (Test-Path $exclude)) { New-Item -ItemType File -Force -Path $exclude | Out-Null }
$existing = @(Get-Content $exclude -ErrorAction SilentlyContinue)
$untracked = @(Git @("ls-files","--others","--exclude-standard"))
foreach ($rel in $untracked) {
    if (-not $rel) { continue }
    $n = ($rel -replace "\\","/")
    if ($existing -notcontains $n) {
        Add-Content -Path $exclude -Value $n
        $existing += $n
    }
}
Log ("PASS: " + $untracked.Count + " untracked tower-only file(s) kept local")

# Runtime-generated tracked files that are allowed to be local state.
$runtimeTrackedPatterns = @(
    '^bridge\.json$',
    '^quant/quant_config\.json$',
    '^quant/.*status.*\.json$',
    '^quant/.*state.*\.json$'
)

$statusNow = @(Git @("status","--short"))
$sourceDirty = @()
foreach ($row in $statusNow) {
    if ($row.Length -lt 4) { continue }
    $path = $row.Substring(3).Trim()
    $norm = $path -replace "\\","/"
    $runtimeGenerated = $false
    foreach ($rx in $runtimeTrackedPatterns) {
        if ($norm -match $rx) { $runtimeGenerated = $true; break }
    }
    if ($runtimeGenerated) {
        $src = Join-Path $Root $path
        if (Test-Path $src -PathType Leaf) {
            $dst = Join-Path $Recovery ("runtime_generated\" + $path)
            New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
            Copy-Item $src $dst -Force
        }
        Git @("restore","--source=HEAD","--staged","--worktree","--",$path) | Out-Null
        $n = ($norm -replace "\\","/")
        if ($existing -notcontains $n) {
            Add-Content -Path $exclude -Value $n
            $existing += $n
        }
        Log ("Preserved runtime-generated tracked file and reset Git copy: " + $norm)
    } else {
        $sourceDirty += $row
    }
}

# Stop all supervisor copies.
$supervisors = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessId -ne $PID -and ([string]$_.CommandLine) -match "(?i)runtime_supervisor_v074\.py"
})
foreach ($p in $supervisors) {
    Log ("Stopping supervisor PID " + $p.ProcessId)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3

$PythonW = Join-Path $Root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $PythonW)) { $PythonW = Join-Path $Root ".venv\Scripts\python.exe" }
$Supervisor = Join-Path $Root "bin\runtime_supervisor_v074.py"
if (-not (Test-Path $PythonW)) { throw "MYLES Python environment missing" }
if (-not (Test-Path $Supervisor)) { throw "Canonical supervisor missing" }

# Start one and remember the exact PID.
$canonical = Start-Process -FilePath $PythonW -ArgumentList $Supervisor -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$canonicalPid = $canonical.Id
Log ("Started canonical supervisor PID " + $canonicalPid)

# Allow competing startup mechanisms to fire. Keep the exact canonical PID if it remains alive.
Start-Sleep -Seconds 18
$rows = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ([string]$_.CommandLine) -match "(?i)runtime_supervisor_v074\.py"
})

$canonicalAlive = @($rows | Where-Object { $_.ProcessId -eq $canonicalPid }).Count -eq 1
if ($rows.Count -gt 1) {
    if ($canonicalAlive) {
        $keepPid = $canonicalPid
    } else {
        $keepPid = ($rows | Sort-Object CreationDate | Select-Object -First 1).ProcessId
        Log ("Canonical PID exited; keeping surviving supervisor PID " + $keepPid)
    }
    foreach ($dup in ($rows | Where-Object { $_.ProcessId -ne $keepPid })) {
        Log ("Stopping duplicate supervisor PID " + $dup.ProcessId)
        Stop-Process -Id $dup.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 4
}

# If no supervisor survived, start one more time after duplicates are gone.
$rows = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ([string]$_.CommandLine) -match "(?i)runtime_supervisor_v074\.py"
})
if ($rows.Count -eq 0) {
    $canonical = Start-Process -FilePath $PythonW -ArgumentList $Supervisor -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    $canonicalPid = $canonical.Id
    Log ("No supervisor survived first pass; restarted canonical supervisor PID " + $canonicalPid)
    Start-Sleep -Seconds 8
}

$runtime = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ([string]$_.CommandLine) -match "(?i)(runtime_supervisor_v074|myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)"
})
$supRows = @($runtime | Where-Object { ([string]$_.CommandLine) -match "runtime_supervisor_v074\.py" })
$quantRows = @($runtime | Where-Object { ([string]$_.CommandLine) -match "quant_service\.mjs" })
$gmxRows = @($runtime | Where-Object { ([string]$_.CommandLine) -match "gmx_live\.mjs.*--daemon" })

function CoreOK {
    try { return $null -ne (Invoke-RestMethod "http://127.0.0.1:8766/health" -TimeoutSec 4) }
    catch { return $false }
}

$core = CoreOK
$listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 8790,8791 })
$p8790 = @($listeners | Where-Object {$_.LocalPort -eq 8790}).Count -gt 0
$p8791 = @($listeners | Where-Object {$_.LocalPort -eq 8791}).Count -gt 0

$after = @(Git @("status","--short"))
$after | Set-Content (Join-Path $Recovery "git_status_after.txt")
$head = ((Git @("rev-parse","--short","HEAD")) -join "").Trim()

Write-Host ""
Write-Host "============================================================"
Write-Host " MYLES FINAL TOWER RESULT"
Write-Host "============================================================"
Write-Host "Git HEAD: $head"
Write-Host "Core 8766 healthy: $core"
Write-Host "Bridge 8790 listening: $p8790"
Write-Host "Gateway 8791 listening: $p8791"
Write-Host "Supervisor count: $($supRows.Count)"
Write-Host "Quant service count: $($quantRows.Count)"
Write-Host "GMX daemon count: $($gmxRows.Count)"
Write-Host "Git working-tree entries: $($after.Count)"
Write-Host "Recovery folder: $Recovery"
if ($after.Count -gt 0) {
    Write-Host "Remaining Git entries:"
    foreach ($row in $after) { Write-Host ("  " + $row) }
}
Write-Host "============================================================"

$pass = $core -and $p8790 -and $p8791 -and $supRows.Count -eq 1 -and $quantRows.Count -eq 1 -and $gmxRows.Count -le 1 -and $after.Count -eq 0

if ($pass) {
    Write-Host ""
    Write-Host "MYLES FINALIZE: PASS" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "MYLES FINALIZE: PARTIAL" -ForegroundColor Yellow
    if ($sourceDirty.Count -gt 0) {
        Write-Host "Real source modifications were preserved and NOT deleted:" -ForegroundColor Yellow
        foreach ($row in $sourceDirty) { Write-Host ("  " + $row) }
    }
}

Write-Host ""
Write-Host "Opening MYLES owner console..."
Start-Sleep -Seconds 2
Start-Process -FilePath (Join-Path $Root "START_MYLESAI.cmd") -WorkingDirectory $Root
