$ErrorActionPreference = "Stop"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$BridgeDir = Join-Path $Root "dashboard_bridge"
$ToolsDir = Join-Path $Root "tools"
$LogsDir = Join-Path $Root "logs"
$DataDir = Join-Path $Root "data"
$Repo = Join-Path $Root "dashboard_site"
$Py = Join-Path $Root ".venv\Scripts\pythonw.exe"
$BridgePy = Join-Path $BridgeDir "dashboard_bridge.py"
$TokenFile = Join-Path $DataDir "dashboard_bridge_token.txt"
$PairFile = Join-Path $DataDir "dashboard_pair_code.json"
$Cloud = Join-Path $ToolsDir "cloudflared.exe"
$TunnelLog = Join-Path $LogsDir "dashboard_tunnel.log"
$DesktopPair = Join-Path ([Environment]::GetFolderPath("Desktop")) "MYLES_DASHBOARD_PAIRING.txt"

New-Item -ItemType Directory -Force -Path $BridgeDir,$ToolsDir,$LogsDir,$DataDir | Out-Null

function New-Secret([int]$Bytes = 32) {
    $buffer = New-Object byte[] $Bytes
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($buffer) } finally { $rng.Dispose() }
    return [Convert]::ToBase64String($buffer).TrimEnd('=').Replace('+','-').Replace('/','_')
}
function New-PairCode {
    $chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    $bytes = New-Object byte[] 8
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    -join ($bytes | ForEach-Object { $chars[$_ % $chars.Length] })
}

if (-not (Test-Path $TokenFile)) {
    (New-Secret 32) | Set-Content -LiteralPath $TokenFile -Encoding ASCII -NoNewline
}
$Token = (Get-Content -LiteralPath $TokenFile -Raw).Trim()
if ($Token.Length -lt 24) { throw "Dashboard bridge token is invalid." }

$PairCode = New-PairCode
$PairExpires = [DateTimeOffset]::UtcNow.AddHours(24).ToUnixTimeSeconds()
$pairJson = @{code=$PairCode;expires_epoch=$PairExpires;created_at=(Get-Date).ToString('o')} | ConvertTo-Json -Compress
[IO.File]::WriteAllText($PairFile, $pairJson, (New-Object Text.UTF8Encoding($false)))

# Stop only bridge/tunnel processes launched from this repair path.
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ([string]$_.CommandLine) -match [regex]::Escape($BridgePy) -or
    (([string]$_.ExecutablePath) -eq $Cloud)
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 500

if (-not (Test-Path $Py)) { throw "Myles Python runtime not found: $Py" }
if (-not (Test-Path $BridgePy)) { throw "Dashboard bridge code not found: $BridgePy" }

$BridgeArgs = @('"' + $BridgePy + '"','--token-file','"' + $TokenFile + '"','--pair-code-file','"' + $PairFile + '"','--port','8790') -join ' '
$BridgeProc = Start-Process -FilePath $Py -ArgumentList $BridgeArgs -WindowStyle Hidden -PassThru

$LocalReady = $false
for ($i=0; $i -lt 20; $i++) {
    try {
        $headers = @{ Authorization = "Bearer $Token" }
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:8790/dashboard/health" -Headers $headers -TimeoutSec 2
        if ($h.bridge.ok) { $LocalReady = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $LocalReady) { throw "Local dashboard bridge did not become healthy." }

if (-not (Test-Path $Cloud)) {
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $Cloud -UseBasicParsing
}
Remove-Item -LiteralPath $TunnelLog -Force -ErrorAction SilentlyContinue
$CloudArgs = "tunnel --url http://127.0.0.1:8790 --no-autoupdate --logfile `"$TunnelLog`" --loglevel info"
$CloudProc = Start-Process -FilePath $Cloud -ArgumentList $CloudArgs -WindowStyle Hidden -PassThru

$PublicUrl = $null
for ($i=0; $i -lt 45; $i++) {
    if (Test-Path $TunnelLog) {
        $raw = Get-Content -LiteralPath $TunnelLog -Raw -ErrorAction SilentlyContinue
        $match = [regex]::Match([string]$raw, 'https://[a-z0-9-]+\.trycloudflare\.com', [Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if ($match.Success) { $PublicUrl = $match.Value.TrimEnd('/'); break }
    }
    if ($CloudProc.HasExited) { break }
    Start-Sleep -Seconds 1
}
if (-not $PublicUrl) { throw "Cloudflare quick tunnel did not return a public HTTPS URL. See $TunnelLog" }

# Verify the public tunnel before publishing it.
$PublicReady = $false
for ($i=0; $i -lt 20; $i++) {
    try {
        $headers = @{ Authorization = "Bearer $Token" }
        $h = Invoke-RestMethod -Uri "$PublicUrl/dashboard/health" -Headers $headers -TimeoutSec 5
        if ($h.bridge.ok) { $PublicReady = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}
if (-not $PublicReady) { throw "Tunnel URL exists but did not pass the authenticated bridge health check." }

$BridgeJson = @{
    url = $PublicUrl
    generated_at = (Get-Date).ToString('o')
    mode = "cloudflare_quick_tunnel"
    auth = "pairing_required"
} | ConvertTo-Json -Depth 4

if (Test-Path (Join-Path $Repo ".git")) {
    [IO.File]::WriteAllText((Join-Path $Repo "bridge.json"), $BridgeJson, (New-Object Text.UTF8Encoding($false)))
    Push-Location $Repo
    try {
        & git.exe add -- bridge.json | Out-Null
        & git.exe diff --cached --quiet
        if ($LASTEXITCODE -ne 0) {
            & git.exe commit -m "Update Myles dashboard bridge endpoint" | Out-Null
            & git.exe pull --rebase origin main | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Could not rebase bridge endpoint onto origin/main." }
            & git.exe push origin main | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Could not publish bridge.json to GitHub." }
        }
    } finally { Pop-Location }
}

$expiresLocal = [DateTimeOffset]::FromUnixTimeSeconds($PairExpires).LocalDateTime
@"
MYLES DASHBOARD PHONE PAIRING
=============================
Dashboard: https://joshuaduskin.github.io/MylesAI/
Bridge:    $PublicUrl
Pair code: $PairCode
Expires:   $expiresLocal

On your phone:
1. Open the Myles Dashboard.
2. Open Chat -> Pair / Configure.
3. The bridge URL should auto-fill. If not, paste the Bridge URL above.
4. Enter the 8-character Pair code and tap Save pairing.

The long access token is never written to GitHub. The dashboard exchanges this short-lived code over HTTPS and stores the token only in that browser.
"@ | Set-Content -LiteralPath $DesktopPair -Encoding UTF8

Write-Output (ConvertTo-Json @{
    ok=$true
    bridge_url=$PublicUrl
    pair_code=$PairCode
    pair_expires=$expiresLocal.ToString('s')
    bridge_pid=$BridgeProc.Id
    tunnel_pid=$CloudProc.Id
    pairing_file=$DesktopPair
} -Compress)
