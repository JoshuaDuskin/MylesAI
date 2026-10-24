[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]{12,64}$')][string]$RequestId,
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$ExpectedHead
)
# Fixed-purpose launcher. No shell command comes from the remote request.
$ErrorActionPreference = "Continue"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$LogDir = Join-Path $Root "logs"
$DataDir = Join-Path $Root "data"
New-Item -ItemType Directory -Force -Path $LogDir, $DataDir | Out-Null
$RunLog = Join-Path $LogDir ("remote_deploy_" + $RequestId + ".log")
$Installed = ""
$ExitCode = 99
$Healthy = $false
try {
    $Updater = Join-Path $Root "UPDATE_TOWER.ps1"
    # A nested PowerShell can allocate its OWN visible console even when its
    # parent was started with CREATE_NO_WINDOW. Hide the child explicitly.
    # Do not run the updater in a native pipeline: hidden services can inherit
    # its pipe handles and keep this receipt writer waiting after it exits.
    # WaitForExit waits for the updater itself, not its long-lived service tree.
    $UpdaterErrorLog = Join-Path $LogDir ("remote_deploy_" + $RequestId + ".err.log")
    $UpdaterArgs = @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-NonInteractive', '-WindowStyle', 'Hidden', '-File', ('"' + $Updater + '"'), '-RemoteQuiet', '-ExpectedHead', $ExpectedHead)
    $UpdaterProcess = Start-Process -FilePath powershell.exe -ArgumentList $UpdaterArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput $RunLog -RedirectStandardError $UpdaterErrorLog
    $null = $UpdaterProcess.Handle
    $UpdaterProcess.WaitForExit()
    $ExitCode = [int]$UpdaterProcess.ExitCode
    $HeadOutput = & git.exe -C $Root rev-parse HEAD 2>$null
    if ($LASTEXITCODE -eq 0) {
        $Installed = ([string]($HeadOutput | Select-Object -First 1)).Trim().ToLowerInvariant()
    }
    try {
        $Health = Invoke-RestMethod -Uri "http://127.0.0.1:8766/health" -TimeoutSec 8
        $Healthy = ($Health.ok -eq $true)
    } catch { $Healthy = $false }
} catch {
    Add-Content -Path $RunLog -Value ("wrapper error: " + $_.Exception.GetType().Name)
} finally {
    $Success = ($ExitCode -eq 0 -and $Healthy -and $Installed -eq $ExpectedHead)
    $Receipt = @{
        request_id = $RequestId
        expected_head = $ExpectedHead
        installed_sha = $Installed
        updater_exit_code = $ExitCode
        health_verified = $Healthy
        success = $Success
        completed_at = (Get-Date).ToUniversalTime().ToString("o")
    }
    try {
        $Temp = Join-Path $DataDir ("remote_deploy_result." + [guid]::NewGuid().ToString("N") + ".tmp")
        $Receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Temp -Encoding UTF8
        Move-Item -LiteralPath $Temp -Destination (Join-Path $DataDir "remote_deploy_result.json") -Force
    } catch {
        Add-Content -Path $RunLog -Value ("receipt error: " + $_.Exception.GetType().Name)
    }
}
if ($Success) { exit 0 } else { exit 1 }
