[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    $elevateArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath)
    $elevated = Start-Process -FilePath "powershell.exe" -ArgumentList $elevateArgs -Verb RunAs -Wait -PassThru
    if ($null -ne $elevated) {
        exit $elevated.ExitCode
    }
    exit 1
}

$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Canonical = "https://github.com/JoshuaDuskin/MylesAI.git"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Recovery = Join-Path $env:LOCALAPPDATA ("MylesAI_Recovery\" + $Stamp)
$Preserve = Join-Path $env:LOCALAPPDATA ("MylesAI_UpdatePreserve_" + $Stamp)
$LogFile = Join-Path $Recovery "tower_update.log"

New-Item -ItemType Directory -Force -Path $Recovery | Out-Null
New-Item -ItemType Directory -Force -Path $Preserve | Out-Null

function Log([string]$Message) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Fail([string]$Message) {
    Log ("FAIL: " + $Message)
    Write-Host ""
    Write-Host "MYLES UPDATE STOPPED" -ForegroundColor Red
    Write-Host $Message -ForegroundColor Red
    Write-Host "Recovery data: $Recovery"
    pause
    exit 1
}

if (-not (Test-Path $Root)) {
    Fail "Canonical tower folder was not found at $Root"
}

$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $GitCommand) {
    Fail "Git is not installed or not available in PATH."
}
$GitExe = $GitCommand.Source

function Invoke-RepoGit {
    param(
        [Parameter(Mandatory=$true)][string[]]$GitArgs,
        [switch]$AllowFailure
    )

    # Windows PowerShell 5.1 can promote native stderr text (including harmless
    # Git warnings such as LF/CRLF conversion notices) into terminating errors
    # when the script-wide ErrorActionPreference is Stop.  Judge Git by its
    # actual process exit code instead.
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & $GitExe -C $Root @GitArgs 2>&1
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }

    if ($code -ne 0 -and -not $AllowFailure) {
        throw ("git " + ($GitArgs -join " ") + " failed with exit code " + $code + ": " + (($output | Out-String).Trim()))
    }

    return @($output | ForEach-Object { [string]$_ })
}

Log "============================================================"
Log "MYLES CANONICAL TOWER UPDATE"
Log "============================================================"
Log "Root: $Root"
Log "Recovery: $Recovery"
Log "Preserve staging: $Preserve"

if (-not (Test-Path (Join-Path $Root ".git"))) {
    Fail "$Root is not a Git repository."
}

try {
    (Invoke-RepoGit -GitArgs @("remote", "-v")) | Set-Content (Join-Path $Recovery "git_remotes_before.txt")
    (Invoke-RepoGit -GitArgs @("status", "--short", "--branch")) | Set-Content (Join-Path $Recovery "git_status_before.txt")
    (Invoke-RepoGit -GitArgs @("rev-parse", "HEAD")) | Set-Content (Join-Path $Recovery "git_head_before.txt")
    Invoke-RepoGit -GitArgs @("bundle", "create", (Join-Path $Recovery "MylesAI_before_update.bundle"), "--all") | Out-Null
    (Invoke-RepoGit -GitArgs @("diff", "--binary")) | Set-Content (Join-Path $Recovery "working_tree_before.patch")
    (Invoke-RepoGit -GitArgs @("diff", "--cached", "--binary")) | Set-Content (Join-Path $Recovery "staged_before.patch")
    Log "PASS: Git history and local tracked changes backed up"
} catch {
    Fail ("Could not create the Git recovery snapshot: " + $_.Exception.Message)
}

$Untracked = @()
try {
    $Untracked = @(Invoke-RepoGit -GitArgs @("ls-files", "--others", "--exclude-standard"))
    $Untracked | Set-Content (Join-Path $Recovery "untracked_before.txt")
} catch {}

$Modified = @()
try {
    $Modified = @(
        (Invoke-RepoGit -GitArgs @("diff", "--name-only", "HEAD")) +
        (Invoke-RepoGit -GitArgs @("diff", "--cached", "--name-only"))
    ) | Where-Object { $_ } | Sort-Object -Unique
    $Modified | Set-Content (Join-Path $Recovery "modified_tracked_before.txt")
} catch {}

$ModifiedCopy = Join-Path $Recovery "modified_tracked_files"
foreach ($rel in $Modified) {
    $src = Join-Path $Root $rel
    if (Test-Path $src -PathType Leaf) {
        $dst = Join-Path $ModifiedCopy $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        Copy-Item $src $dst -Force
    }
}
Log "PASS: modified tracked source files preserved separately"

Log "Stopping MYLES runtime processes before switching source..."
$processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $cmd = [string]$_.CommandLine
    $name = [string]$_.Name
    $_.ProcessId -ne $PID -and (
        $cmd -like ("*" + $Root + "*") -or
        $cmd -match "(?i)(runtime_supervisor_v074|runtime_supervisor\.py|myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)" -or
        ($name -ieq "cloudflared.exe" -and $cmd -match "8791")
    )
}

foreach ($proc in $processes) {
    try {
        Log ("Stopping {0} PID {1}" -f $proc.Name, $proc.ProcessId)
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    } catch {}
}
Start-Sleep -Seconds 2

function Move-ToPreserve {
    param([string]$RelativePath, [string]$PreserveName)
    $src = Join-Path $Root $RelativePath
    if (-not (Test-Path $src)) { return $false }
    $dst = Join-Path $Preserve $PreserveName
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Move-Item -Path $src -Destination $dst -Force
    Log ("Preserved local runtime path: " + $RelativePath)
    return $true
}

function Restore-FromPreserve {
    param([string]$RelativePath, [string]$PreserveName)
    $src = Join-Path $Preserve $PreserveName
    if (-not (Test-Path $src)) { return $false }
    $dst = Join-Path $Root $RelativePath
    if (Test-Path $dst) {
        Remove-Item $dst -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Move-Item -Path $src -Destination $dst -Force
    Log ("Restored local runtime path: " + $RelativePath)
    return $true
}

Move-ToPreserve ".venv" "venv" | Out-Null
Move-ToPreserve "data" "data" | Out-Null
Move-ToPreserve "logs" "logs" | Out-Null
Move-ToPreserve "backups" "backups" | Out-Null
Move-ToPreserve "self_updates" "self_updates" | Out-Null
Move-ToPreserve "quant\node_modules" "quant_node_modules" | Out-Null

if (Test-Path (Join-Path $Root "bin\cloudflared.exe")) {
    Move-ToPreserve "bin\cloudflared.exe" "cloudflared.exe" | Out-Null
} elseif (Test-Path (Join-Path $Root "tools\cloudflared.exe")) {
    Move-ToPreserve "tools\cloudflared.exe" "cloudflared.exe" | Out-Null
}

if (Test-Path (Join-Path $Root "dashboard_site")) {
    Move-ToPreserve "dashboard_site" "dashboard_site_before" | Out-Null
}

Get-ChildItem $Root -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "dashboard_site_legacy_*" } |
    ForEach-Object {
        $dst = Join-Path $Recovery $_.Name
        Move-Item $_.FullName $dst -Force
        Log ("Archived stale dashboard checkout: " + $_.Name)
    }

$EnvFiles = @()
Get-ChildItem $Root -File -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like ".env*" } |
    ForEach-Object {
        $dst = Join-Path $Preserve ("env\" + $_.Name)
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        Move-Item $_.FullName $dst -Force
        $EnvFiles += $_.Name
        Log ("Preserved local environment file: " + $_.Name)
    }

$LocalOnlyStage = Join-Path $Preserve "local_only"
foreach ($rel in $Untracked) {
    if (-not $rel) { continue }
    if ($rel -match "^(?i)(data|logs|backups|self_updates|\.venv|quant/node_modules|dashboard_site)(/|\\)") { continue }
    $src = Join-Path $Root $rel
    if (-not (Test-Path $src -PathType Leaf)) { continue }
    $dst = Join-Path $LocalOnlyStage $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Move-Item $src $dst -Force
}
if (Test-Path $LocalOnlyStage) {
    Log "PASS: local-only files staged safely outside the source tree"
}

try {
    Log "Pointing tower at canonical GitHub repository..."
    Invoke-RepoGit -GitArgs @("remote", "set-url", "origin", $Canonical) | Out-Null
    Invoke-RepoGit -GitArgs @("fetch", "origin", "main", "--prune") | Out-Null
    Invoke-RepoGit -GitArgs @("checkout", "-B", "main", "origin/main", "--force") | Out-Null
    Invoke-RepoGit -GitArgs @("reset", "--hard", "origin/main") | Out-Null
    Log "PASS: tracked source now matches JoshuaDuskin/MylesAI main"
} catch {
    Fail ("Canonical source sync failed: " + $_.Exception.Message)
}

Restore-FromPreserve ".venv" "venv" | Out-Null
Restore-FromPreserve "data" "data" | Out-Null
Restore-FromPreserve "logs" "logs" | Out-Null
Restore-FromPreserve "backups" "backups" | Out-Null
Restore-FromPreserve "self_updates" "self_updates" | Out-Null
Restore-FromPreserve "quant\node_modules" "quant_node_modules" | Out-Null

$Cloudflared = Join-Path $Preserve "cloudflared.exe"
if (Test-Path $Cloudflared) {
    $dst = Join-Path $Root "bin\cloudflared.exe"
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Move-Item $Cloudflared $dst -Force
    Log "Restored local cloudflared.exe"
}

foreach ($name in $EnvFiles) {
    $src = Join-Path $Preserve ("env\" + $name)
    if (Test-Path $src) {
        Move-Item $src (Join-Path $Root $name) -Force
        Log ("Restored local environment file: " + $name)
    }
}

$RestoredLocalOnly = @()
if (Test-Path $LocalOnlyStage) {
    Get-ChildItem $LocalOnlyStage -File -Recurse -Force | ForEach-Object {
        $rel = $_.FullName.Substring($LocalOnlyStage.Length).TrimStart("\")
        $dst = Join-Path $Root $rel
        if (-not (Test-Path $dst)) {
            New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
            Move-Item $_.FullName $dst -Force
            $RestoredLocalOnly += $rel
        } else {
            $conflict = Join-Path $Recovery ("local_only_conflicts\" + $rel)
            New-Item -ItemType Directory -Force -Path (Split-Path $conflict -Parent) | Out-Null
            Move-Item $_.FullName $conflict -Force
        }
    }
}
$RestoredLocalOnly | Set-Content (Join-Path $Recovery "local_only_restored.txt")
if ($RestoredLocalOnly.Count -gt 0) {
    $InfoExclude = Join-Path $Root ".git\info\exclude"
    New-Item -ItemType Directory -Force -Path (Split-Path $InfoExclude -Parent) | Out-Null
    if (-not (Test-Path $InfoExclude)) {
        New-Item -ItemType File -Force -Path $InfoExclude | Out-Null
    }
    $ExistingExcludes = @(Get-Content $InfoExclude -ErrorAction SilentlyContinue)
    foreach ($rel in $RestoredLocalOnly) {
        $normalized = ($rel -replace "\\","/")
        if ($ExistingExcludes -notcontains $normalized) {
            Add-Content -Path $InfoExclude -Value $normalized
            $ExistingExcludes += $normalized
        }
    }
    Log ("Restored " + $RestoredLocalOnly.Count + " local-only file(s) and kept them local via .git/info/exclude")
}

$Data = Join-Path $Root "data"
New-Item -ItemType Directory -Force -Path $Data | Out-Null

foreach ($stale in @(
    "supervisor.pid",
    "supervisor.lock",
    "core.pid",
    "gmx_live_daemon.pid"
)) {
    Remove-Item (Join-Path $Data $stale) -Force -ErrorAction SilentlyContinue
}

function New-RandomToken {
    $bytes = New-Object byte[] 48
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    return ([Convert]::ToBase64String($bytes)).TrimEnd([char]"=").Replace("+","-").Replace("/","_")
}

$PairFile = Join-Path $Data "dashboard_pair_code.json"
$PinnedPairFile = Join-Path $Data "dashboard_pair_code_pinned.txt"
$PairCode = ""

if (Test-Path $PinnedPairFile) {
    try { $PairCode = (Get-Content $PinnedPairFile -Raw).Trim().ToUpperInvariant() } catch {}
}
if (-not $PairCode -and (Test-Path $PairFile)) {
    try {
        $pairExisting = Get-Content $PairFile -Raw | ConvertFrom-Json
        $PairCode = ([string]$pairExisting.code).Trim().ToUpperInvariant()
    } catch {}
}

if ($PairCode -match "^[A-Z0-9]{8}$") {
    $pairObject = [ordered]@{
        code = $PairCode
        created_at = [DateTimeOffset]::UtcNow.ToString("o")
        expires_epoch = [DateTimeOffset]::UtcNow.AddYears(2).ToUnixTimeSeconds()
        pinned = $true
    }
    $pairObject | ConvertTo-Json | Set-Content $PairFile -Encoding UTF8
    Set-Content $PinnedPairFile -Value $PairCode -Encoding ASCII -NoNewline
    Log "PASS: existing 8-character dashboard pairing code preserved and re-pinned"
} else {
    Log "WARNING: no valid pinned 8-character pairing code was found; existing pairing file was left unchanged"
}

Set-Content (Join-Path $Data "dashboard_bridge_token.txt") -Value (New-RandomToken) -Encoding ASCII -NoNewline
Set-Content (Join-Path $Data "dashboard_public_read_token.txt") -Value (New-RandomToken) -Encoding ASCII -NoNewline
Remove-Item (Join-Path $Data "tunnel_state.json") -Force -ErrorAction SilentlyContinue
Log "PASS: dashboard bridge credentials rotated locally; pairing code itself was not changed"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$PythonW = Join-Path $Root ".venv\Scripts\pythonw.exe"

if (-not (Test-Path $Python)) {
    Fail "Preserved MYLES Python environment did not restore correctly."
}
if (-not (Test-Path $PythonW)) {
    $PythonW = $Python
}

$QuantNodeModules = Join-Path $Root "quant\node_modules"
if (-not (Test-Path $QuantNodeModules)) {
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npm -and (Test-Path (Join-Path $Root "quant\package-lock.json"))) {
        Log "Quant node_modules was missing; rebuilding from package-lock.json"
        Push-Location (Join-Path $Root "quant")
        try {
            & $npm.Source ci
            if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }
        } finally {
            Pop-Location
        }
        Log "PASS: Quant dependencies rebuilt"
    } else {
        Log "WARNING: Quant node_modules is missing and npm/package-lock was unavailable"
    }
}

$Supervisor = Join-Path $Root "bin\runtime_supervisor_v074.py"
if (-not (Test-Path $Supervisor)) {
    Fail "Canonical runtime supervisor is missing after update."
}

Log "Enforcing a single canonical supervisor..."
$SupervisorPidFile = Join-Path $Data "runtime_supervisor_v074.pid"
$SupervisorPids = @()

if (Test-Path $SupervisorPidFile) {
    try {
        $pidFromFile = [int](Get-Content $SupervisorPidFile -Raw).Trim()
        if ($pidFromFile -gt 0) { $SupervisorPids += $pidFromFile }
    } catch {}
}

$ExistingSupervisors = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.ProcessId -ne $PID -and ([string]$_.CommandLine) -match "(?i)runtime_supervisor_v074\.py"
})
$SupervisorPids += @($ExistingSupervisors | ForEach-Object { [int]$_.ProcessId })

foreach ($supervisorPid in ($SupervisorPids | Sort-Object -Unique)) {
    if ($supervisorPid -le 0 -or $supervisorPid -eq $PID) { continue }
    try {
        Log ("Stopping existing supervisor PID " + $supervisorPid + " before starting replacement")
        Stop-Process -Id $supervisorPid -Force -ErrorAction SilentlyContinue
        & taskkill.exe /PID $supervisorPid /T /F *> $null
    } catch {}
}

$supervisorDeadline = (Get-Date).AddSeconds(15)
$RemainingSupervisors = @()
do {
    $RemainingSupervisors = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessId -ne $PID -and ([string]$_.CommandLine) -match "(?i)runtime_supervisor_v074\.py"
    })
    if ($RemainingSupervisors.Count -eq 0) { break }
    Start-Sleep -Seconds 1
} while ((Get-Date) -lt $supervisorDeadline)

if ($RemainingSupervisors.Count -gt 0) {
    Fail "An older MYLES supervisor could not be stopped; refusing to start a second mutex owner."
}

$SupervisorStdOut = Join-Path $Root "logs\runtime_supervisor_startup.out.log"
$SupervisorStdErr = Join-Path $Root "logs\runtime_supervisor_startup.err.log"
Remove-Item $SupervisorStdOut, $SupervisorStdErr -Force -ErrorAction SilentlyContinue
$CanonicalSupervisor = Start-Process -FilePath $PythonW -ArgumentList $Supervisor -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $SupervisorStdOut -RedirectStandardError $SupervisorStdErr -PassThru
$CanonicalSupervisorPid = $CanonicalSupervisor.Id
Log ("Started canonical hidden supervisor PID " + $CanonicalSupervisorPid)
Start-Sleep -Seconds 3

$SupervisorAlive = $false
try {
    $SupervisorAlive = $null -ne (Get-Process -Id $CanonicalSupervisorPid -ErrorAction Stop)
} catch {}

if (-not $SupervisorAlive) {
    $startupError = ""
    if (Test-Path $SupervisorStdErr) {
        $startupError = ((Get-Content $SupervisorStdErr -Tail 40 -ErrorAction SilentlyContinue) -join " ")
    }
    if ($startupError) {
        Log ("FAIL: supervisor exited during startup: " + $startupError)
    } else {
        Log "FAIL: supervisor exited during startup without stderr output"
    }
    Fail "The canonical supervisor exited during startup. See $SupervisorStdErr"
}

$GameWatcher = Get-ChildItem (Join-Path $Root "bin") -File -Filter "game_mode_watch*.py" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if ($GameWatcher) {
    $already = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        ([string]$_.CommandLine) -match [regex]::Escape($GameWatcher.FullName)
    })
    if ($already.Count -eq 0) {
        Start-Process -FilePath $PythonW -ArgumentList $GameWatcher.FullName -WorkingDirectory (Split-Path $GameWatcher.FullName -Parent) -WindowStyle Hidden | Out-Null
        Log ("Started preserved Game Mode watcher: " + $GameWatcher.Name)
    }
}

function Core-Healthy {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:8766/health" -TimeoutSec 3
        return ($null -ne $r)
    } catch {
        return $false
    }
}

$deadline = (Get-Date).AddSeconds(75)
while ((Get-Date) -lt $deadline) {
    if (Core-Healthy) { break }
    Start-Sleep -Seconds 2
}

$CoreOK = Core-Healthy
$Port8790 = $false
$Port8791 = $false
$serviceDeadline = (Get-Date).AddSeconds(70)
while ((Get-Date) -lt $serviceDeadline) {
    $Listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 8790,8791 })
    $Port8790 = @($Listeners | Where-Object { $_.LocalPort -eq 8790 }).Count -gt 0
    $Port8791 = @($Listeners | Where-Object { $_.LocalPort -eq 8791 }).Count -gt 0
    if ($Port8790 -and $Port8791) { break }
    Start-Sleep -Seconds 2
}
if ($Port8790 -and $Port8791) {
    Start-Sleep -Seconds 5
}

$RuntimeProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ([string]$_.CommandLine) -match "(?i)(runtime_supervisor_v074|myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)"
})

$GmxCount = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "gmx_live\.mjs.*--daemon" }).Count
$SupervisorRows = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "runtime_supervisor_v074\.py" })
if ($SupervisorRows.Count -gt 1) {
    $canonicalAlive = @($SupervisorRows | Where-Object { $_.ProcessId -eq $CanonicalSupervisorPid }).Count -eq 1
    if ($canonicalAlive) {
        foreach ($dup in ($SupervisorRows | Where-Object { $_.ProcessId -ne $CanonicalSupervisorPid })) {
            Log ("Stopping duplicate supervisor PID " + $dup.ProcessId)
            Stop-Process -Id $dup.ProcessId -Force -ErrorAction SilentlyContinue
            & taskkill.exe /PID $dup.ProcessId /T /F *> $null
        }
        Start-Sleep -Seconds 3
        $RuntimeProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            ([string]$_.CommandLine) -match "(?i)(runtime_supervisor_v074|myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)"
        })
        $SupervisorRows = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "runtime_supervisor_v074\.py" })
    } else {
        Log "FAIL: canonical supervisor PID exited while an older supervisor remained; refusing to keep the stale process"
        foreach ($stale in $SupervisorRows) {
            Stop-Process -Id $stale.ProcessId -Force -ErrorAction SilentlyContinue
            & taskkill.exe /PID $stale.ProcessId /T /F *> $null
        }
        $SupervisorRows = @()
    }
} elseif ($SupervisorRows.Count -eq 0) {
    Log "FAIL: no canonical supervisor was present at final runtime verification"
}
$SupervisorCount = $SupervisorRows.Count
$QuantCount = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "quant_service\.mjs" }).Count

$Head = ((Invoke-RepoGit -GitArgs @("rev-parse", "--short", "HEAD")) -join "").Trim()
$Origin = ((Invoke-RepoGit -GitArgs @("remote", "get-url", "origin")) -join "").Trim()
$GitStatus = @(Invoke-RepoGit -GitArgs @("status", "--short"))
$GitStatus | Set-Content (Join-Path $Recovery "git_status_after.txt")
if ($GitStatus.Count -gt 0) {
    Log "Git working-tree entries after update:"
    foreach ($entry in $GitStatus) { Log ("  " + $entry) }
}

$Summary = @()
$Summary += "============================================================"
$Summary += " MYLES TOWER UPDATE RESULT"
$Summary += "============================================================"
$Summary += "Canonical repo: $Origin"
$Summary += "Git HEAD: $Head"
$Summary += "Core 8766 healthy: $CoreOK"
$Summary += "Bridge 8790 listening: $Port8790"
$Summary += "Gateway 8791 listening: $Port8791"
$Summary += "Supervisor count: $SupervisorCount"
$Summary += "Quant service count: $QuantCount"
$Summary += "GMX daemon count: $GmxCount"
$Summary += "Local-only files restored: $($RestoredLocalOnly.Count)"
$Summary += "Recovery folder: $Recovery"
$Summary += "Git working-tree entries after update: $($GitStatus.Count)"
$Summary += "============================================================"

$Summary | Tee-Object -FilePath (Join-Path $Recovery "RESULT.txt") | ForEach-Object { Write-Host $_ }

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs") | Out-Null
Copy-Item $LogFile (Join-Path $Root "logs\tower_update_latest.log") -Force
Copy-Item (Join-Path $Recovery "RESULT.txt") (Join-Path $Root "logs\tower_update_RESULT.txt") -Force

if ($CoreOK -and $Port8790 -and $Port8791 -and $SupervisorCount -eq 1 -and $GmxCount -le 1) {
    Write-Host ""
    Write-Host "MYLES TOWER UPDATE: PASS" -ForegroundColor Green
    Write-Host "The canonical runtime is back online." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "MYLES TOWER UPDATE: PARTIAL" -ForegroundColor Yellow
    Write-Host "The source update completed, but one or more runtime checks still need attention." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Saved result:" -ForegroundColor Cyan
Write-Host (Join-Path $Root "logs\tower_update_RESULT.txt")
Write-Host "Saved log:" -ForegroundColor Cyan
Write-Host (Join-Path $Root "logs\tower_update_latest.log")
Write-Host ""
Write-Host "THIS POWERSHELL WINDOW WILL STAY OPEN." -ForegroundColor Yellow
Write-Host "Copy the result above now. The MYLES dashboard will not open until you press ENTER." -ForegroundColor Yellow
[void](Read-Host "Press ENTER only after you are finished copying the result")

Write-Host ""
Write-Host "Starting the single owner console..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process -FilePath (Join-Path $Root "START_MYLESAI.cmd") -WorkingDirectory $Root
