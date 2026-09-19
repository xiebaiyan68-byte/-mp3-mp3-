$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\api-host"
if (-not (Test-Path .\node_modules\NeteaseCloudMusicApi\app.js)) {
  npm install --omit=dev
}
Write-Host "Starting NeteaseCloudMusicApi at http://127.0.0.1:3000"
node .\node_modules\NeteaseCloudMusicApi\app.js
