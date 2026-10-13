[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Flag = Join-Path $Root "data\remote_deploy_enabled.json"
@{ enabled = $false; disabled_at = (Get-Date).ToUniversalTime().ToString("o") } |
    ConvertTo-Json | Set-Content -LiteralPath $Flag -Encoding UTF8
Unregister-ScheduledTask -TaskName "MylesAI Remote Deploy Poll" -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "MYLES REMOTE DEPLOY: DISABLED" -ForegroundColor Yellow
