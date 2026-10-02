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
    $elevateArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-File", $PSCommandPath)
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

# Retire the specific legacy per-user auto-launcher that creates a second
# supervisor outside the canonical update/owner-console path. Preserve its
# exact value in recovery before removing it.
$RunKeyPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
try {
    $legacyRun = Get-ItemProperty -Path $RunKeyPath -Name "MylesRuntimeSupervisor" -ErrorAction SilentlyContinue
    $legacyRunValue = [string]$legacyRun.MylesRuntimeSupervisor
    if ($legacyRunValue -and $legacyRunValue -match "(?i)runtime_supervisor_v074\.py" -and $legacyRunValue -match [regex]::Escape($Root)) {
        Set-Content -Path (Join-Path $Recovery "legacy_MylesRuntimeSupervisor_RunValue.txt") -Value $legacyRunValue -Encoding UTF8
        Remove-ItemProperty -Path $RunKeyPath -Name "MylesRuntimeSupervisor" -Force -ErrorAction Stop
        Log "PASS: removed legacy HKCU Run supervisor launcher; value backed up in recovery"
    } elseif ($legacyRunValue) {
        Log "WARNING: left unrelated MylesRuntimeSupervisor Run value unchanged"
    }
} catch {
    Log ("WARNING: could not retire legacy HKCU Run supervisor launcher: " + $_.Exception.Message)
}

# Retire every known old MYLES auto-launch path that can race the canonical
# supervisor. Previous builds used Run/RunOnce, Startup-folder files, and
# Scheduled Tasks. Keep a recovery record before removing only entries that
# explicitly point at this MYLES root and a retired launcher/supervisor.
$AutoLaunchPattern = "(?i)(runtime_supervisor(?:_v074)?\.py|START_MYLESAI\.cmd|launch_myles\.py|myles_console(?:_v074)?\.py)"
$RunKeyCandidates = @(
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
)
foreach ($key in $RunKeyCandidates) {
    try {
        $props = Get-ItemProperty -Path $key -ErrorAction SilentlyContinue
        if ($null -eq $props) { continue }
        foreach ($prop in $props.PSObject.Properties) {
            if ($prop.Name -match "^PS(Path|ParentPath|ChildName|Drive|Provider)$") { continue }
            $value = [string]$prop.Value
            if ($value -and $value -match [regex]::Escape($Root) -and $value -match $AutoLaunchPattern) {
                Add-Content -Path (Join-Path $Recovery "retired_autolaunch_registry.txt") -Value ("{0} :: {1}={2}" -f $key,$prop.Name,$value)
                Remove-ItemProperty -Path $key -Name $prop.Name -Force -ErrorAction SilentlyContinue
                Log ("PASS: retired legacy auto-launch registry value " + $prop.Name)
            }
        }
    } catch {
        Log ("WARNING: registry auto-launch cleanup failed for " + $key + ": " + $_.Exception.Message)
    }
}

try {
    $startupFolders = @(
        [Environment]::GetFolderPath("Startup"),
        [Environment]::GetFolderPath("CommonStartup")
    ) | Where-Object { $_ -and (Test-Path $_) } | Sort-Object -Unique
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in $startupFolders) {
        Get-ChildItem $folder -File -ErrorAction SilentlyContinue | ForEach-Object {
            $evidence = ""
            if ($_.Extension -ieq ".lnk") {
                try {
                    $shortcut = $shell.CreateShortcut($_.FullName)
                    $evidence = ([string]$shortcut.TargetPath + " " + [string]$shortcut.Arguments)
                } catch {}
            } elseif ($_.Extension -match "(?i)\.(cmd|bat|vbs|ps1)$") {
                try { $evidence = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue } catch {}
            }
            if ($evidence -and $evidence -match [regex]::Escape($Root) -and $evidence -match $AutoLaunchPattern) {
                Add-Content -Path (Join-Path $Recovery "retired_autolaunch_startup.txt") -Value $_.FullName
                Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
                Log ("PASS: retired legacy Startup launcher " + $_.Name)
            }
        }
    }
} catch {
    Log ("WARNING: Startup-folder cleanup failed: " + $_.Exception.Message)
}

try {
    Get-ScheduledTask -ErrorAction SilentlyContinue | ForEach-Object {
        $task = $_
        $evidence = (($task.Actions | ForEach-Object { ([string]$_.Execute + " " + [string]$_.Arguments) }) -join " ")
        if ($evidence -and $evidence -match [regex]::Escape($Root) -and $evidence -match $AutoLaunchPattern) {
            Add-Content -Path (Join-Path $Recovery "retired_autolaunch_tasks.txt") -Value ($task.TaskPath + $task.TaskName + " :: " + $evidence)
            Unregister-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -Confirm:$false -ErrorAction SilentlyContinue
            Log ("PASS: retired legacy scheduled launcher " + $task.TaskPath + $task.TaskName)
        }
    }
} catch {
    Log ("WARNING: scheduled-task cleanup failed: " + $_.Exception.Message)
}

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
        $cmd -match "(?i)(runtime_supervisor_v074|runtime_supervisor\.py|myles_core\.py|myles_console_v074|myles_console\.py|START_MYLESAI\.cmd|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)" -or
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

function Stop-ProcessTreeQuiet {
    param([int]$ProcessId)

    if ($ProcessId -le 0 -or $ProcessId -eq $PID) { return }
    try {
        $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
        if ($taskkill) {
            Start-Process -FilePath $taskkill.Source -ArgumentList @("/PID", "$ProcessId", "/T", "/F") -WindowStyle Hidden -Wait -ErrorAction SilentlyContinue | Out-Null
        }
    } catch {}
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
        Stop-ProcessTreeQuiet $supervisorPid
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

# Forced termination may prevent an old supervisor from deleting its filesystem
# lock/PID marker. With no supervisor process left, both markers are stale.
Remove-Item (Join-Path $Data "runtime_supervisor_v074.lock") -Force -ErrorAction SilentlyContinue
Remove-Item $SupervisorPidFile -Force -ErrorAction SilentlyContinue
Log "PASS: cleared stale supervisor lock/PID markers after confirming no supervisor is running"

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

# A uv-backed Windows venv legitimately shows TWO process rows for one Python
# program: the .venv launcher and its uv-managed CPython child. Count supervisor
# ownership from the authoritative PID file + lock, not raw process rows.
$SupervisorOwnerPid = 0
$SupervisorOwnerOK = $false
$SupervisorProcessChainCount = 0
$ownerDeadline = (Get-Date).AddSeconds(25)
while ((Get-Date) -lt $ownerDeadline) {
    $RuntimeProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        ([string]$_.CommandLine) -match "(?i)(runtime_supervisor_v074|myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)"
    })
    $SupervisorRows = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "runtime_supervisor_v074\.py" })
    $SupervisorProcessChainCount = $SupervisorRows.Count

    if (Test-Path $SupervisorPidFile) {
        try { $SupervisorOwnerPid = [int](Get-Content $SupervisorPidFile -Raw).Trim() } catch { $SupervisorOwnerPid = 0 }
    }
    if ($SupervisorOwnerPid -gt 0) {
        $OwnerRow = @($SupervisorRows | Where-Object { [int]$_.ProcessId -eq $SupervisorOwnerPid })
        if ($OwnerRow.Count -eq 1) {
            $SupervisorOwnerOK = $true
            break
        }
    }
    Start-Sleep -Seconds 1
}

if (-not $SupervisorOwnerOK) {
    Log "Supervisor owner PID was not healthy after startup; performing one clean restart"
    foreach ($row in @($SupervisorRows)) {
        try {
            Stop-Process -Id ([int]$row.ProcessId) -Force -ErrorAction SilentlyContinue
            Stop-ProcessTreeQuiet ([int]$row.ProcessId)
        } catch {}
    }
    Start-Sleep -Seconds 2
    Remove-Item (Join-Path $Data "runtime_supervisor_v074.lock") -Force -ErrorAction SilentlyContinue
    Remove-Item $SupervisorPidFile -Force -ErrorAction SilentlyContinue
    $CanonicalSupervisor = Start-Process -FilePath $PythonW -ArgumentList $Supervisor -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $SupervisorStdOut -RedirectStandardError $SupervisorStdErr -PassThru
    Log ("Restarted canonical supervisor launcher PID " + $CanonicalSupervisor.Id)

    $ownerDeadline = (Get-Date).AddSeconds(25)
    while ((Get-Date) -lt $ownerDeadline) {
        Start-Sleep -Seconds 1
        $RuntimeProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            ([string]$_.CommandLine) -match "(?i)(runtime_supervisor_v074|myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)"
        })
        $SupervisorRows = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "runtime_supervisor_v074\.py" })
        $SupervisorProcessChainCount = $SupervisorRows.Count
        if (Test-Path $SupervisorPidFile) {
            try { $SupervisorOwnerPid = [int](Get-Content $SupervisorPidFile -Raw).Trim() } catch { $SupervisorOwnerPid = 0 }
        }
        if ($SupervisorOwnerPid -gt 0 -and @($SupervisorRows | Where-Object { [int]$_.ProcessId -eq $SupervisorOwnerPid }).Count -eq 1) {
            $SupervisorOwnerOK = $true
            break
        }
    }
}

if ($SupervisorOwnerOK) {
    $SupervisorCount = 1
    Log ("PASS: one logical supervisor owner PID " + $SupervisorOwnerPid + "; interpreter process chain count " + $SupervisorProcessChainCount)
} else {
    $SupervisorCount = 0
    Log "FAIL: no healthy authoritative supervisor owner PID was published"
    foreach ($row in @($SupervisorRows)) {
        Log ("Supervisor evidence PID " + $row.ProcessId + " parent=" + $row.ParentProcessId + " :: " + ([string]$row.CommandLine))
    }
}

$QuantCount = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "quant_service\.mjs" }).Count
$CopyCount = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "copy_trader_service\.mjs.*--daemon" }).Count

# If the supervisor survived but a Node worker did not come up during the first
# service cycle, start that missing worker once here. The supervisor will adopt
# it on the next cycle and its process guard prevents duplicates.
$GameModeNow = $false
try {
    $gamePathNow = Join-Path $Data "game_mode_state.json"
    if (Test-Path $gamePathNow) {
        $gameStateNow = Get-Content $gamePathNow -Raw -ErrorAction Stop | ConvertFrom-Json
        $GameModeNow = [bool]$gameStateNow.active
    }
} catch {}

if (-not $GameModeNow) {
    $NodeCandidates = @()
    $nodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($nodeCmd) { $NodeCandidates += $nodeCmd.Source }
    if ($env:ProgramFiles) { $NodeCandidates += (Join-Path $env:ProgramFiles "nodejs\node.exe") }
    if (${env:ProgramFiles(x86)}) { $NodeCandidates += (Join-Path ${env:ProgramFiles(x86)} "nodejs\node.exe") }
    if ($env:LOCALAPPDATA) { $NodeCandidates += (Join-Path $env:LOCALAPPDATA "Programs\nodejs\node.exe") }
    if ($env:NVM_SYMLINK) { $NodeCandidates += (Join-Path $env:NVM_SYMLINK "node.exe") }
    $NodeExe = $NodeCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

    if ($NodeExe) {
        $QuantDir = Join-Path $Root "quant"
        if ($QuantCount -eq 0 -and (Test-Path (Join-Path $QuantDir "quant_service.mjs"))) {
            Log "Quant worker was absent after supervisor startup; starting one verified fallback instance"
            Start-Process -FilePath $NodeExe -ArgumentList "quant_service.mjs" -WorkingDirectory $QuantDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root "logs\quant_startup.out.log") -RedirectStandardError (Join-Path $Root "logs\quant_startup.err.log") | Out-Null
        }
        if ($GmxCount -eq 0 -and (Test-Path (Join-Path $QuantDir "gmx_live.mjs"))) {
            Log "GMX daemon was absent after supervisor startup; starting one verified fallback instance"
            Start-Process -FilePath $NodeExe -ArgumentList @("gmx_live.mjs","--daemon") -WorkingDirectory $QuantDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root "logs\gmx_live_startup.out.log") -RedirectStandardError (Join-Path $Root "logs\gmx_live_startup.err.log") | Out-Null
        }
        if ($CopyCount -eq 0 -and (Test-Path (Join-Path $QuantDir "copy_trader_service.mjs"))) {
            Log "Copy research daemon was absent after supervisor startup; starting one verified fallback instance"
            Start-Process -FilePath $NodeExe -ArgumentList @("copy_trader_service.mjs","--daemon") -WorkingDirectory $QuantDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root "logs\copy_trader_startup.out.log") -RedirectStandardError (Join-Path $Root "logs\copy_trader_startup.err.log") | Out-Null
        }
        Start-Sleep -Seconds 8
        $RuntimeProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            ([string]$_.CommandLine) -match "(?i)(runtime_supervisor_v074|myles_core\.py|dashboard_bridge\.py|public_gateway_v074\.py|quant_service\.mjs|gmx_live\.mjs|copy_trader_service\.mjs|game_mode_watch)"
        })
        $SupervisorRows = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "runtime_supervisor_v074\.py" })
        $SupervisorCount = $SupervisorRows.Count
        $QuantCount = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "quant_service\.mjs" }).Count
        $GmxCount = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "gmx_live\.mjs.*--daemon" }).Count
        $CopyCount = @($RuntimeProcesses | Where-Object { ([string]$_.CommandLine) -match "copy_trader_service\.mjs.*--daemon" }).Count
    } else {
        Log "FAIL: Node.js executable was not found; Quant/GMX workers cannot run"
    }
}

# Verify the actual dashboard data path, not just listening ports/process names.
$DashboardStatusOK = $false
$QuantFeedOK = $false
$GmxMarketCount = 0
$DashboardStatusAgeSeconds = $null
$DashboardStatusError = ""
$GameModeActive = $false
try {
    $gamePath = Join-Path $Data "game_mode_state.json"
    if (Test-Path $gamePath) {
        $gameState = Get-Content $gamePath -Raw -ErrorAction Stop | ConvertFrom-Json
        $GameModeActive = [bool]$gameState.active
    }
} catch {}

$ReadToken = ""
try { $ReadToken = (Get-Content (Join-Path $Data "dashboard_public_read_token.txt") -Raw -ErrorAction Stop).Trim() } catch {}
$statusDeadline = (Get-Date).AddSeconds(180)
while ((Get-Date) -lt $statusDeadline) {
    try {
        if (-not $ReadToken) { throw "public read token unavailable" }
        $headers = @{ "X-Myles-Read" = $ReadToken; "Accept" = "application/json" }
        $status = Invoke-RestMethod -Uri "http://127.0.0.1:8791/dashboard/status" -Headers $headers -TimeoutSec 20
        $generated = [DateTimeOffset]::Parse([string]$status.generated_at)
        $DashboardStatusAgeSeconds = [math]::Round(([DateTimeOffset]::UtcNow - $generated.ToUniversalTime()).TotalSeconds, 1)
        $DashboardStatusOK = ($DashboardStatusAgeSeconds -ge -30 -and $DashboardStatusAgeSeconds -le 90 -and [bool]$status.myles.online)
        $trading = $status.trading
        $QuantFeedOK = $false
        $GmxMarketCount = 0
        if ($null -ne $trading) {
            $QuantFeedOK = ([bool]$trading._verified -and ([string]$trading._verified_source -eq "data/trading_status.json"))
            if ($null -ne $trading.markets) { $GmxMarketCount = @($trading.markets).Count }
        }
        if ($DashboardStatusOK -and ($GameModeActive -or ($QuantFeedOK -and $GmxMarketCount -gt 0))) {
            break
        }
        $DashboardStatusError = if (-not $DashboardStatusOK) { "dashboard status not fresh/core online" } elseif (-not $QuantFeedOK) { "Quant telemetry not verified" } else { "GMX markets empty" }
    } catch {
        $DashboardStatusError = $_.Exception.Message
    }
    Start-Sleep -Seconds 3
}
if ($DashboardStatusOK) {
    Log ("PASS: gateway dashboard status is fresh; age=" + $DashboardStatusAgeSeconds + "s")
} else {
    Log ("FAIL: gateway dashboard status verification failed: " + $DashboardStatusError)
}
if ($GameModeActive) {
    Log "INFO: Gaming Performance Mode is active; Quant/GMX workers are intentionally paused"
} elseif ($QuantFeedOK -and $GmxMarketCount -gt 0) {
    Log ("PASS: verified Quant telemetry with " + $GmxMarketCount + " GMX market(s)")
} else {
    Log ("FAIL: Quant/GMX telemetry is not healthy: " + $DashboardStatusError)
}

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
$Summary += "Supervisor interpreter process chain count: $SupervisorProcessChainCount"
$Summary += "Quant service count: $QuantCount"
$Summary += "GMX daemon count: $GmxCount"
$Summary += "Copy research daemon count: $CopyCount"
$Summary += "Dashboard live status verified: $DashboardStatusOK"
$Summary += "Dashboard status age seconds: $DashboardStatusAgeSeconds"
$Summary += "Gaming Performance Mode active: $GameModeActive"
$Summary += "Quant feed verified: $QuantFeedOK"
$Summary += "GMX market count: $GmxMarketCount"
$Summary += "Local-only files restored: $($RestoredLocalOnly.Count)"
$Summary += "Recovery folder: $Recovery"
$Summary += "Git working-tree entries after update: $($GitStatus.Count)"
$Summary += "============================================================"

$Summary | Tee-Object -FilePath (Join-Path $Recovery "RESULT.txt") | ForEach-Object { Write-Host $_ }

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs") | Out-Null
Copy-Item $LogFile (Join-Path $Root "logs\tower_update_latest.log") -Force
Copy-Item (Join-Path $Recovery "RESULT.txt") (Join-Path $Root "logs\tower_update_RESULT.txt") -Force

$DataPlaneOK = $DashboardStatusOK -and ($GameModeActive -or ($QuantFeedOK -and $GmxMarketCount -gt 0))
if ($CoreOK -and $Port8790 -and $Port8791 -and $SupervisorCount -eq 1 -and $GmxCount -le 1 -and $DataPlaneOK) {
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
Write-Host "The update result is saved. Launching the single owner console automatically..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "Starting the single owner console..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

# Launch through an explicit persistent cmd.exe host. Calling a .cmd file
# directly with Start-Process can return to PowerShell immediately on some
# Windows builds, leaving the owner console invisible or already closed.
$OwnerLauncher = Join-Path $Root "START_MYLESAI.cmd"
$OwnerCommand = 'call "' + $OwnerLauncher + '"'
try {
    Start-Process -FilePath $env:ComSpec -ArgumentList @("/d", "/k", $OwnerCommand) -WorkingDirectory $Root -WindowStyle Normal | Out-Null
    Write-Host "Owner console launched in a persistent Command Prompt window." -ForegroundColor Green
} catch {
    Write-Host ("Could not launch the owner console: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "Run this manually if needed: $OwnerLauncher" -ForegroundColor Yellow
}
