$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\api-host"
$node = Join-Path $PSScriptRoot "runtime\node.exe"
if (-not (Test-Path $node)) { $node = "node" }
if (-not (Test-Path .\node_modules\NeteaseCloudMusicApi\app.js)) {
  if ($node -eq "node") { npm install --omit=dev } else { throw "Bundled API dependencies are missing." }
}
Write-Host "Starting NeteaseCloudMusicApi at http://127.0.0.1:3000"
& $node .\node_modules\NeteaseCloudMusicApi\app.js
