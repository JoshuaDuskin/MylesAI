$ErrorActionPreference = "Stop"
$Root = Join-Path $env:LOCALAPPDATA "MylesAI"
$Quant = Join-Path $Root "quant"
$LogDir = Join-Path $Root "logs"
$Log = Join-Path $LogDir "quant.log"
$ErrLog = Join-Path $LogDir "quant-error.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Node = (Get-Command node.exe -ErrorAction Stop).Source
if (-not (Test-Path (Join-Path $Quant "quant_service.mjs"))) { throw "Myles Quant service missing: $Quant" }

# One quant service only.
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    ([string]$_.CommandLine) -match [regex]::Escape((Join-Path $Quant "quant_service.mjs"))
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 350

$proc = Start-Process -FilePath $Node -ArgumentList 'quant_service.mjs' -WorkingDirectory $Quant -WindowStyle Hidden -RedirectStandardOutput $Log -RedirectStandardError $ErrLog -PassThru
Write-Output (ConvertTo-Json @{ok=$true;pid=$proc.Id;service=(Join-Path $Quant "quant_service.mjs");log=$Log;error_log=$ErrLog} -Compress)
