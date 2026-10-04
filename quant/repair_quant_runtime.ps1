# Canonical MYLES Quant one-pass repair. Paper history is preserved; live stays locked.
$ErrorActionPreference = "Stop"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Quant = Join-Path $Root "quant"
$Data = Join-Path $Root "data"
$Logs = Join-Path $Root "logs"
$StatusFile = Join-Path $Data "trading_status.json"
$ConfigFile = Join-Path $Quant "quant_config.json"
$QuantSource = Join-Path $Quant "quant_service.mjs"
$GmxSource = Join-Path $Quant "gmx_live.mjs"
$CopySource = Join-Path $Quant "copy_trader_service.mjs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

function Step([string]$Message) { Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Message) }
function NodePath {
    $cmd = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($candidate in @((Join-Path $env:ProgramFiles "nodejs\node.exe"),(Join-Path $env:LOCALAPPDATA "Programs\node\node.exe"))) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw "Node.js was not found."
}
function ReadStatus {
    if (-not (Test-Path -LiteralPath $StatusFile)) { return $null }
    try { return Get-Content -LiteralPath $StatusFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}
function PinPairing {
    $file = Join-Path $Data "dashboard_pair_code.json"
    if (-not (Test-Path -LiteralPath $file)) { return }
    $pair = Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $pair.code) { return }
    $pair.pinned = $true
    $pair.expires_epoch = 0
    $tmp = "$file.tmp"
    ($pair | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $file -Force
    Write-Host "PASS: existing local pairing code pinned indefinitely."
}
function Set-Prop($Object,[string]$Name,$Value) {
    if (-not $Object) { return }
    $property = $Object.PSObject.Properties[$Name]
    if ($property) { $property.Value = $Value }
    else { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value }
}
function PinScalpPaperConfig {
    if (-not (Test-Path -LiteralPath $ConfigFile)) { return }
    $cfg = Get-Content -LiteralPath $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
    Set-Prop $cfg "timeframe" "1m"
    Set-Prop $cfg "poll_seconds" 30
    $paper = $cfg.paper
    if (-not $paper) { $paper = [pscustomobject]@{}; Set-Prop $cfg "paper" $paper }
    Set-Prop $paper "enabled" $true
    Set-Prop $paper "auto_trading_enabled" $true
    Set-Prop $paper "adaptive_strategy_selection" $true
    Set-Prop $paper "require_candidate_evidence" $true
    Set-Prop $paper "min_forward_stress_return_pct" 0
    Set-Prop $paper "emergency_stop" $false
    $research = $cfg.research_exploration
    if (-not $research) { $research = [pscustomobject]@{}; Set-Prop $cfg "research_exploration" $research }
    Set-Prop $research "enabled" $true
    Set-Prop $research "continuous_market_research_enabled" $true
    Set-Prop $research "paper_lab_enabled" $true
    Set-Prop $research "tournament_enabled" $true
    Set-Prop $research "interval_seconds" 120
    $validation = $cfg.validation
    if (-not $validation) { $validation = [pscustomobject]@{}; Set-Prop $cfg "validation" $validation }
    Set-Prop $validation "min_base_return_pct" 0
    Set-Prop $validation "min_stress_return_pct" 0
    $live = $cfg.live_execution
    if (-not $live) { $live = [pscustomobject]@{}; Set-Prop $cfg "live_execution" $live }
    Set-Prop $live "enabled" $false
    Set-Prop $live "signing_enabled" $false
    Set-Prop $live "reason" "Live execution remains hard-locked until owner review and forward-paper validation."
    $tmp = "$ConfigFile.tmp"
    ($cfg | ConvertTo-Json -Depth 30) | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $ConfigFile -Force
    Write-Host "PASS: 1-minute scalp paper loop and continuous research pinned; live execution locked."
}
function StopQuant {
    $rows = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine -match "quant_service\.mjs" })
    foreach ($row in $rows) { Stop-Process -Id ([int]$row.ProcessId) -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 800
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
    $stdout = Join-Path $Logs "quant_repair_stdout.log"
    $stderr = Join-Path $Logs "quant_repair_stderr.log"
    $proc = Start-Process -FilePath $node -ArgumentList @("quant_service.mjs") -WorkingDirectory $Quant -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    if (-not $proc) { throw "Quant worker did not start." }
    return $proc.Id
}
function WaitFresh([string]$Before,[int]$Seconds=90) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $status = ReadStatus
        if ($status -and $status.generated_at -and ([string]$status.generated_at -ne $Before)) {
            try {
                $age = ((Get-Date).ToUniversalTime() - [DateTime]::Parse($status.generated_at).ToUniversalTime()).TotalSeconds
                if ($age -ge -5 -and $age -le 180) { return $status }
            } catch {}
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    return (ReadStatus)
}
function Age($Status) {
    if (-not $Status -or -not $Status.generated_at) { return $null }
    try { return [math]::Round(((Get-Date).ToUniversalTime() - [DateTime]::Parse($Status.generated_at).ToUniversalTime()).TotalSeconds,1) } catch { return $null }
}

try {
    Write-Host "============================================================"
    Write-Host " MYLES QUANT REPAIR - ONE PASS"
    Write-Host "============================================================"
    Write-Host ("Root: {0}" -f $Root)
    Write-Host "Paper history is preserved. Live money remains disarmed."
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($git -and (Test-Path -LiteralPath (Join-Path $Root ".git"))) {
        Step "Updating canonical source"
        & $git.Source -C $Root fetch origin main
        & $git.Source -C $Root checkout main
        & $git.Source -C $Root pull --ff-only origin main
        if ($LASTEXITCODE -ne 0) { throw "Canonical source update failed." }
    }
    PinPairing
    Step "Checking Quant, GMX, and trader-feed source"
    CheckSources
    $beforeStatus = ReadStatus
    $before = if ($beforeStatus) { [string]$beforeStatus.generated_at } else { "" }
    Step "Stopping old Quant workers only"
    StopQuant
    # Pin after stopping Quant so an old worker cannot rewrite the config
    # between the repair and the new worker's first cycle.
    PinScalpPaperConfig
    Step "Starting one Quant worker"
    $pid = StartQuant
    Write-Host ("Quant PID: {0}" -f $pid)
    Step "Waiting for fresh paper telemetry"
    $status = WaitFresh $before 90
    if (-not $status) { throw "Trading telemetry was not produced." }
    $age = Age $status
    $markets = @($status.markets).Count
    $trades = @($status.recent_trades).Count
    $positions = @($status.positions).Count
    $cycle = if ($status.runtime_activity) { $status.runtime_activity.cycle } else { 0 }
    $engine = if ($status.engine) { $status.engine.status } else { "missing" }
    $locked = [bool]$status.execution_locked
    $actualTimeframe = if ($status.configuration) { [string]$status.configuration.timeframe } else { "missing" }
    $gate = if ($status.research_runtime) { $status.research_runtime.paper_entry_gate } else { $null }
    $gateStatus = if ($gate) { [string]$gate.status } else { "missing" }
    $gateEligible = if ($gate) { [int]$gate.eligible_candidates } else { 0 }
    Write-Host ""
    Write-Host "============================================================"
    Write-Host " MYLES QUANT REPAIR RESULT"
    Write-Host "============================================================"
    Write-Host ("Telemetry age seconds: {0}" -f $age)
    Write-Host ("Engine status: {0}" -f $engine)
    Write-Host ("Mode: {0}" -f $status.mode)
    Write-Host ("Execution locked: {0}" -f $locked)
    Write-Host ("GMX markets: {0}" -f $markets)
    Write-Host ("Quant cycle: {0}" -f $cycle)
    Write-Host ("Recent paper trades: {0}" -f $trades)
    Write-Host ("Open paper positions: {0}" -f $positions)
    Write-Host ("Timeframe: {0}" -f $actualTimeframe)
    Write-Host ("Paper entry evidence gate: {0}" -f $gateStatus)
    Write-Host ("Evidence-qualified candidates: {0}" -f $gateEligible)
    Write-Host "============================================================"
    if (-not $status -or $age -eq $null -or $age -gt 180 -or $markets -lt 1 -or $engine -ne "running" -or -not $locked -or $actualTimeframe -ne "1m") { throw "Quant did not produce fresh locked 1m paper telemetry. Inspect $Logs." }
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
