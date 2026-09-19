$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$appPath = Join-Path $PSScriptRoot "dist\NetEasePlaylistBackup.exe"
$apiScript = Join-Path $PSScriptRoot "start_api.ps1"
if (-not (Test-Path -LiteralPath $appPath)) {
  throw "Desktop application was not found: $appPath"
}
$api = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if (-not $api) {
  Start-Process powershell -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-File',$apiScript) -WindowStyle Hidden
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { break }
  }
}
Start-Process -FilePath $appPath -WorkingDirectory $PSScriptRoot
