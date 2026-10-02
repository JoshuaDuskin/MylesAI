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
$GitExe = (Get-Command git.exe -ErrorAction Stop).Source

function Invoke-Git {
    param([string[]]$A)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $o = & $GitExe -C $Root @A 2>&1
        $c = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
    if ($c -ne 0) { throw ("git " + ($A -join " ") + " failed: " + (($o | Out-String).Trim())) }
    return @($o | ForEach-Object { [string]$_ })
}

Log "============================================================"
Log "MYLES FINAL CANONICAL CLEANUP V3"
Log "============================================================"

@(Invoke-Git @("status","--short","--branch")) | Set-Content (Join-Path $Recovery "git_status_before.txt")

# Preserve the live Quant configuration before Git stops tracking it.
$QuantConfig = Join-Path $Root "quant\quant_config.json"
$SavedQuantConfig = Join-Path $Recovery "quant_config.live.json"
if (Test-Path $QuantConfig -PathType Leaf) {
    Copy-Item $QuantConfig $SavedQuantConfig -Force
    Log "PASS: live Quant config preserved"
}

# Sync canonical source where stale nested repositories and quant_config are no longer tracked.
Invoke-Git @("remote","set-url","origin","https://github.com/JoshuaDuskin/MylesAI.git") | Out-Null
Invoke-Git @("fetch","origin","main","--prune") | Out-Null
Invoke-Git @("checkout","-B","main","origin/main","--force") | Out-Null
Invoke-Git @("reset","--hard","origin/main") | Out-Null
Log "PASS: source reset to canonical MylesAI/main"

# Restore live tower configuration after the source reset.
if (Test-Path $SavedQuantConfig) {
    New-Item -ItemType Directory -Force -Path (Split-Path $QuantConfig -Parent) | Out-Null
    Copy-Item $SavedQuantConfig $QuantConfig -Force
    Log "PASS: live Quant config restored as tower-local state"
}

# Local nested repositories/workspaces are preserved by design. The canonical
# .gitignore now excludes them, but add them to local exclude as a second guard.
$Exclude = Join-Path $Root ".git\info\exclude"
New-Item -ItemType Directory -Force -Path (Split-Path $Exclude -Parent) | Out-Null
if (-not (Test-Path $Exclude)) { New-Item -ItemType File -Force -Path $Exclude | Out-Null }
$LocalPatterns = @(
    "dashboard_site/",
    "workspace/",
    "legacy_repo_cleanup_v055/",
    "legacy_repo_cleanup_v056/",
    "quant/quant_config.json"
)
$Existing = @(Get-Content $Exclude -ErrorAction SilentlyContinue)
foreach ($pattern in $LocalPatterns) {
    if ($Existing -notcontains $pattern) {
        Add-Content -Path $Exclude -Value $pattern
        $Existing += $pattern
    }
}

# Also keep any other genuinely untracked tower-only files local.
$Untracked = @(Invoke-Git @("ls-files","--others","--exclude-standard"))
foreach ($rel in $Untracked) {
    if (-not $rel) { continue }
    $n = ($rel -replace "\\","/")
    if ($Existing -notcontains $n) {
        Add-Content -Path $Exclude -Value $n
        $Existing += $n
    }
}
Log ("PASS: tower-only paths preserved locally")

# Stop all currently visible supervisor wrapper/child processes. This is safe:
# children such as core/Quant/bridge are intentionally left running.
$SupervisorRows = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessId -ne $PID -and ([string]$_.CommandLine) -match "(?i)runtime_supervisor_v074\.py"
})
foreach ($p in $SupervisorRows) {
    Log ("Stopping supervisor process PID " + $p.ProcessId)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3

$PidFile = Join-Path $Root "data\runtime_supervisor_v074.pid"
Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

$PythonW = Join-Path $Root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $PythonW)) { $PythonW = Join-Path $Root ".venv\Scripts\python.exe" }
$Supervisor = Join-Path $Root "bin\runtime_supervisor_v074.py"
if (-not (Test-Path $PythonW)) { throw "MYLES Python environment missing" }
if (-not (Test-Path $Supervisor)) { throw "Canonical supervisor missing" }

Start-Process -FilePath $PythonW -ArgumentList $Supervisor -WorkingDirectory $Root -WindowStyle Hidden | Out-Null
Log "Started canonical supervisor"

# Wait for the actual Python supervisor process to publish its authoritative PID.
$deadline = (Get-Date).AddSeconds(20)
$SupervisorPid = 0
while ((Get-Date) -lt $deadline) {
    if (Test-Path $PidFile) {
        try { $SupervisorPid = [int](Get-Content $PidFile -Raw).Trim() } catch { $SupervisorPid = 0 }
        if ($SupervisorPid -gt 0) {
            $alive = Get-Process -Id $SupervisorPid -ErrorAction SilentlyContinue
            if ($alive) { break }
        }
    }
    Start-Sleep -Seconds 1
}

$SupervisorAlive = $false
if ($SupervisorPid -gt 0) {
    $SupervisorAlive = $null -ne (Get-Process -Id $SupervisorPid -ErrorAction SilentlyContinue)
}

# Give competing startup paths time to try. The global mutex should make their
# real supervisor child exit without replacing the authoritative PID file.
Start-Sleep -Seconds 10
if (Test-Path $PidFile) {
    try {
        $PublishedPid = [int](Get-Content $PidFile -Raw).Trim()
        if ($PublishedPid -gt 0) {
            $SupervisorPid = $PublishedPid
            $SupervisorAlive = $null -ne (Get-Process -Id $SupervisorPid -ErrorAction SilentlyContinue)
        }
    } catch {}
}

$Runtime = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ([string]$_.CommandLine) -match "(?i)(myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)"
})
$QuantRows = @($Runtime | Where-Object { ([string]$_.CommandLine) -match "quant_service\.mjs" })
$GmxRows = @($Runtime | Where-Object { ([string]$_.CommandLine) -match "gmx_live\.mjs.*--daemon" })

function CoreOK {
    try { return $null -ne (Invoke-RestMethod "http://127.0.0.1:8766/health" -TimeoutSec 4) }
    catch { return $false }
}
$Core = CoreOK
$Listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 8790,8791 })
$P8790 = @($Listeners | Where-Object {$_.LocalPort -eq 8790}).Count -gt 0
$P8791 = @($Listeners | Where-Object {$_.LocalPort -eq 8791}).Count -gt 0

$LiveStatus = $false
$QuantVerified = $false
$GmxMarketCount = 0
$GameModeActive = $false
try {
    $gamePath = Join-Path $Root "data\game_mode_state.json"
    if (Test-Path $gamePath) {
        $gameState = Get-Content $gamePath -Raw | ConvertFrom-Json
        $GameModeActive = [bool]$gameState.active
    }
} catch {}
try {
    $read = (Get-Content (Join-Path $Root "data\dashboard_public_read_token.txt") -Raw -ErrorAction Stop).Trim()
    if ($read) {
        $statusDeadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $statusDeadline) {
            try {
                $status = Invoke-RestMethod "http://127.0.0.1:8791/dashboard/status" -Headers @{"X-Myles-Read"=$read;"Accept"="application/json"} -TimeoutSec 20
                $generated = [DateTimeOffset]::Parse([string]$status.generated_at)
                $age = ([DateTimeOffset]::UtcNow - $generated.ToUniversalTime()).TotalSeconds
                $LiveStatus = ($age -ge -30 -and $age -le 90 -and [bool]$status.myles.online)
                if ($null -ne $status.trading) {
                    $QuantVerified = ([bool]$status.trading._verified -and ([string]$status.trading._verified_source -eq "data/trading_status.json"))
                    if ($null -ne $status.trading.markets) { $GmxMarketCount = @($status.trading.markets).Count }
                }
                if ($LiveStatus -and ($GameModeActive -or ($QuantVerified -and $GmxMarketCount -gt 0))) { break }
            } catch {}
            Start-Sleep -Seconds 3
        }
    }
} catch {}

$After = @(Invoke-Git @("status","--short"))
$After | Set-Content (Join-Path $Recovery "git_status_after.txt")
$Head = ((Invoke-Git @("rev-parse","--short","HEAD")) -join "").Trim()

Write-Host ""
Write-Host "============================================================"
Write-Host " MYLES FINAL TOWER RESULT V3"
Write-Host "============================================================"
Write-Host "Git HEAD: $Head"
Write-Host "Core 8766 healthy: $Core"
Write-Host "Bridge 8790 listening: $P8790"
Write-Host "Gateway 8791 listening: $P8791"
Write-Host "Supervisor PID: $SupervisorPid"
Write-Host "Logical supervisor healthy: $SupervisorAlive"
Write-Host "Quant service count: $($QuantRows.Count)"
Write-Host "GMX daemon count: $($GmxRows.Count)"
Write-Host "Dashboard live status verified: $LiveStatus"
Write-Host "Gaming Performance Mode active: $GameModeActive"
Write-Host "Quant feed verified: $QuantVerified"
Write-Host "GMX market count: $GmxMarketCount"
Write-Host "Git working-tree entries: $($After.Count)"
Write-Host "Recovery folder: $Recovery"
if ($After.Count -gt 0) {
    Write-Host "Remaining Git entries:"
    foreach ($row in $After) { Write-Host ("  " + $row) }
}
Write-Host "============================================================"

$DataPlaneOK = $LiveStatus -and ($GameModeActive -or ($QuantVerified -and $GmxMarketCount -gt 0))
$Pass = $Core -and $P8790 -and $P8791 -and $SupervisorAlive -and $QuantRows.Count -eq 1 -and $GmxRows.Count -le 1 -and $DataPlaneOK -and $After.Count -eq 0

if ($Pass) {
    Write-Host ""
    Write-Host "MYLES FINALIZE V3: PASS" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "MYLES FINALIZE V3: PARTIAL" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Opening MYLES owner console..."
Start-Sleep -Seconds 2
Start-Process -FilePath (Join-Path $Root "START_MYLESAI.cmd") -WorkingDirectory $Root
