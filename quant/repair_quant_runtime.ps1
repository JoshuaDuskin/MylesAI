# Canonical MYLES Quant repair and verification.
$ErrorActionPreference = "Stop"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Quant = Join-Path $Root "quant"
$Data = Join-Path $Root "data"
$Logs = Join-Path $Root "logs"
$StatusFile = Join-Path $Data "trading_status.json"
$StartScript = Join-Path $Quant "start_quant.ps1"
$QuantSource = Join-Path $Quant "quant_service.mjs"
$GmxSource = Join-Path $Quant "gmx_live.mjs"
$CopySource = Join-Path $Quant "copy_trader_service.mjs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

function Step([string]$Message) { Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message) }
function ReadStatus {
    if (-not (Test-Path -LiteralPath $StatusFile)) { return $null }
    try { return (Get-Content -LiteralPath $StatusFile -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}
function NodePath {
    $cmd = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidate = Join-Path $env:ProgramFiles "nodejs\node.exe"
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    $candidate = Join-Path $env:LOCALAPPDATA "Programs\node\node.exe"
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    throw "Node.js was not found."
}
function StopQuant {
    $rows = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and $_.CommandLine -match "quant_service\.mjs"
    })
    foreach ($row in $rows) { Stop-Process -Id ([int]$row.ProcessId) -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 750
}
function CheckSources {
    $node = NodePath
    foreach ($file in @($QuantSource,$GmxSource,$CopySource)) {
        if (-not (Test-Path -LiteralPath $file)) { throw "Missing Quant source: $file" }
        & $node --check $file
        if ($LASTEXITCODE -ne 0) { throw "Node syntax check failed: $file" }
    }
}
function StartQuant {
    $node = NodePath
    if (-not (Test-Path -LiteralPath $QuantSource)) { throw "Missing Quant source: $QuantSource" }
    $stdout = Join-Path $Logs "quant_repair_stdout.log"
    $stderr = Join-Path $Logs "quant_repair_stderr.log"
    $proc = Start-Process -FilePath $node -ArgumentList @("quant_service.mjs") -WorkingDirectory $Quant -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    if (-not $proc) { throw "Quant worker did not start." }
    return @{ pid = $proc.Id; stdout = $stdout; stderr = $stderr }
}
function WaitStatus([int]$Seconds,[string]$BeforeGeneratedAt) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $json = ReadStatus
        if ($json -and $json.generated_at) {
            try {
                $age = ((Get-Date).ToUniversalTime() - [DateTime]::Parse($json.generated_at).ToUniversalTime()).TotalSeconds
                $changed = ([string]$json.generated_at -ne [string]$BeforeGeneratedAt)
                if ($changed -and $age -ge -5 -and $age -le 180) { return $json }
            } catch {}
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    return (ReadStatus)
}
function Age($Json) {
    if (-not $Json -or -not $Json.generated_at) { return $null }
    try { return [math]::Round(((Get-Date).ToUniversalTime() - [DateTime]::Parse($Json.generated_at).ToUniversalTime()).TotalSeconds,1) } catch { return $null }
}
function PinLocalPairingCode {
    $pairFile = Join-Path $Data "dashboard_pair_code.json"
    if (-not (Test-Path -LiteralPath $pairFile)) { return }
    try {
        $pair = Get-Content -LiteralPath $pairFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($pair.code) {
            $pair.pinned = $true
            $pair.expires_epoch = 0
            $tmp = $pairFile + ".tmp"
            ($pair | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $tmp -Encoding UTF8
            Move-Item -LiteralPath $tmp -Destination $pairFile -Force
            Write-Host "PASS: existing local pairing code pinned indefinitely."
        }
    } catch {
        Write-Host "Pairing file was not changed: $($_.Exception.Message)"
    }
}

try {
    Write-Host "============================================================"
    Write-Host " MYLES QUANT REPAIR AND VERIFICATION"
    Write-Host "============================================================"
    Write-Host ("Root: {0}" -f $Root)
    Write-Host "Paper history is preserved. Live money remains disarmed."

    Step "Updating canonical source"
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($git -and (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
        & $git.Source -C $Root fetch origin main
        & $git.Source -C $Root checkout main
        & $git.Source -C $Root pull --ff-only origin main
        if ($LASTEXITCODE -ne 0) { throw "Canonical source update failed." }
    }
    $head = "unknown"
    if ($git -and (Test-Path -LiteralPath (Join-Path $Root ".git"))) { $head = (& $git.Source -C $Root rev-parse --short HEAD).Trim() }
    Write-Host ("Installed source commit: {0}" -f $head)
    PinLocalPairingCode

    Step "Checking Quant, GMX, and copy-research source"
    CheckSources
    Write-Host "PASS: Node syntax checks passed."

    $beforeStatus = ReadStatus
    $beforeGeneratedAt = ""
    if ($beforeStatus -and $beforeStatus.generated_at) { $beforeGeneratedAt = [string]$beforeStatus.generated_at }

    Step "Stopping old Quant workers only"
    StopQuant
    Step "Starting one Quant worker"
    $launch = StartQuant
    if ($launch -and $launch.pid) { Write-Host ("Quant PID: {0}" -f $launch.pid) }

    Step "Waiting for fresh paper telemetry"
    $status = WaitStatus 75 $beforeGeneratedAt
    $age = Age $status
    $markets = 0
    $trades = 0
    $positions = 0
    $cycle = 0
    $candidates = 0
    $validated = 0
    $engine = "missing"
    $mode = "unknown"
    $locked = $false
    $paperEnabled = $false
    $researchEnabled = $false
    if ($status) {
        $markets = @($status.markets).Count
        $trades = @($status.recent_trades).Count
        $positions = @($status.positions).Count
        if ($status.runtime_activity) { $cycle = $status.runtime_activity.cycle }
        if ($status.validation) { $candidates = $status.validation.candidate_total; $validated = $status.validation.candidate_pass_count }
        if ($status.engine) { $engine = $status.engine.status }
        $mode = $status.mode
        $locked = [bool]$status.execution_locked
        if ($status.controls -and $status.controls.paper_trading_bot) { $paperEnabled = [bool]$status.controls.paper_trading_bot.enabled }
        if ($status.controls -and $status.controls.continuous_market_research) { $researchEnabled = [bool]$status.controls.continuous_market_research.enabled }
    }

    Write-Host ""
    Write-Host "============================================================"
    Write-Host " MYLES QUANT REPAIR RESULT"
    Write-Host "============================================================"
    Write-Host ("Installed source commit: {0}" -f $head)
    Write-Host ("Telemetry age seconds: {0}" -f $age)
    Write-Host ("Engine status: {0}" -f $engine)
    Write-Host ("Mode: {0}" -f $mode)
    Write-Host ("Execution locked: {0}" -f $locked)
    Write-Host ("GMX markets: {0}" -f $markets)
    Write-Host ("Quant cycle: {0}" -f $cycle)
    Write-Host ("Recent paper trades in telemetry: {0}" -f $trades)
    Write-Host ("Open paper positions: {0}" -f $positions)
    Write-Host ("Candidates / validated: {0} / {1}" -f $candidates,$validated)
    Write-Host ("Paper bot enabled: {0}" -f $paperEnabled)
    Write-Host ("Continuous research enabled: {0}" -f $researchEnabled)
    Write-Host "============================================================"

    if (-not $status -or $age -eq $null -or $age -gt 180 -or $markets -lt 1 -or $engine -ne "running" -or -not $locked) {
        throw "Quant did not produce fresh locked paper telemetry. Inspect $Logs."
    }
    Write-Host "SUCCESS: Quant is running with fresh GMX-backed paper telemetry."
    Write-Host ("Quant log: {0}" -f (Join-Path $Logs "quant.log"))
    Write-Host ("Quant errors: {0}" -f (Join-Path $Logs "quant-error.log"))
    exit 0
} catch {
    Write-Host ""
    Write-Host "MYLES QUANT REPAIR FAILED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ("Inspect logs in: {0}" -f $Logs)
    exit 1
}
