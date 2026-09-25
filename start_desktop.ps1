$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$runtime = Join-Path $PSScriptRoot "runtime"
if (Test-Path (Join-Path $runtime "ffmpeg.exe")) { $env:Path = "$runtime;$env:Path" }
$ffmpeg = Join-Path $runtime "ffmpeg.exe"
$mutex = New-Object System.Threading.Mutex($false, 'NetEasePlaylistBackup.SingleInstance')
if (-not $mutex.WaitOne(0)) {
  Write-Host "NetEasePlaylistBackup is already starting or running."
  exit 0
}
$appCandidates = @(
  (Join-Path $PSScriptRoot "NetEasePlaylistBackup.exe"),
  (Join-Path $PSScriptRoot "dist\NetEasePlaylistBackup.exe")
)
$appPath = $appCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$apiScript = Join-Path $PSScriptRoot "start_api.ps1"
if (-not (Test-Path -LiteralPath $appPath)) {
  throw "Desktop application was not found. Put NetEasePlaylistBackup.exe beside START_APP.cmd or under dist\"
}
$running = Get-CimInstance Win32_Process -Filter "name='NetEasePlaylistBackup.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.ExecutablePath -eq (Resolve-Path -LiteralPath $appPath).Path }
if ($running) {
  Write-Host "NetEasePlaylistBackup is already running. Reusing the existing window."
  exit 0
}
$api = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if (-not $api) {
  Start-Process powershell -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-File',$apiScript) -WindowStyle Hidden
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { break }
  }
}
if (Test-Path $ffmpeg) { $env:NETEASE_FFMPEG = $ffmpeg }
Start-Process -FilePath $appPath -WorkingDirectory $PSScriptRoot
