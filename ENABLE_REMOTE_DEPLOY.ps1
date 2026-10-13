[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Agent = Join-Path $Root "bin\remote_deploy_agent.py"
$Apply = Join-Path $Root "bin\remote_deploy_apply.ps1"
$PythonW = Join-Path $Root ".venv\Scripts\pythonw.exe"
$Flag = Join-Path $Root "data\remote_deploy_enabled.json"
$TaskName = "MylesAI Remote Deploy Poll"
$Repo = "https://github.com/JoshuaDuskin/MylesAI.git"

if (-not (Test-Path $Agent -PathType Leaf) -or -not (Test-Path $Apply -PathType Leaf)) {
    throw "Remote deployment source missing. Run the existing canonical updater first."
}
if (-not (Test-Path $PythonW -PathType Leaf)) {
    throw "Myles Python environment missing."
}
$OriginOutput = & git.exe -C $Root remote get-url origin 2>$null
$Origin = ([string]($OriginOutput | Select-Object -First 1)).Trim()
if ($LASTEXITCODE -ne 0 -or $Origin -ne $Repo) {
    throw "Tower's Git origin is not the canonical MylesAI HTTPS repository."
}

$Action = New-ScheduledTaskAction -Execute $PythonW -Argument ('"' + $Agent + '"') -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$Principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "Myles owner-approved GitHub main deployment poller; no incoming network port." -Force | Out-Null

New-Item -ItemType Directory -Force -Path (Split-Path $Flag -Parent) | Out-Null
@{ enabled = $true; auto_update = $true; canonical = $Repo; enabled_at = (Get-Date).ToUniversalTime().ToString("o") } |
    ConvertTo-Json | Set-Content -LiteralPath $Flag -Encoding UTF8

Write-Host "MYLES CI-VERIFIED AUTO UPDATE: ENABLED" -ForegroundColor Green
Write-Host "Task: $TaskName (hidden, every 5 minutes while signed in)"
Write-Host "Auto-updates: only new GitHub main commits with passing Validate MYLES Runtime CI."
Write-Host "No special GitHub request, remote shell, arbitrary commands, or open ports."
Write-Host "Status: $Root\data\remote_deploy_state.json"
Write-Host "Disable anytime with DISABLE_REMOTE_DEPLOY.ps1"
$Probe = Join-Path $Root "bin\remote_deploy_smoketest.py"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if ((Test-Path -LiteralPath $Python) -and (Test-Path -LiteralPath $Probe)) {
    & $Python $Probe
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Scheduled task registered but CI reachability or source approval is not yet verified." -ForegroundColor Yellow
    }
}
