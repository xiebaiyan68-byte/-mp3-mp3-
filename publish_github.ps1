$ErrorActionPreference = "Stop"
param(
    [Parameter(Mandatory = $true)]
    [string]$Repository,
    [string]$ReleaseTag = "v1.0.0",
    [switch]$CreatePrivate,
    [switch]$SkipRelease
)

Set-Location $PSScriptRoot

function Invoke-Gh {
    & gh @args
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub CLI command failed: gh $($args -join ' ')"
    }
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    $ghPath = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path $ghPath) { $env:Path += ";C:\Program Files\GitHub CLI" }
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI not found. Install it with: winget install --id GitHub.cli --exact"
}

gh auth status
git status --short

if (-not (git remote get-url origin 2>$null)) {
    $visibility = if ($CreatePrivate) { "--private" } else { "--public" }
    Invoke-Gh repo create $Repository $visibility --source . --remote origin --push
} else {
    git push -u origin main
}

if (-not $SkipRelease) {
    $asset = Join-Path $PSScriptRoot "NetEasePlaylistBackup-v1.0.0-windows.zip"
    if (-not (Test-Path $asset)) {
        & $PSScriptRoot\build_windows.ps1
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
        & $PSScriptRoot\START_APP.cmd /? | Out-Null
        throw "Build completed. Create the release zip first, then rerun with -SkipRelease:$false."
    }
    $existing = gh release view $ReleaseTag --repo $Repository 2>$null
    if ($LASTEXITCODE -eq 0) {
        Invoke-Gh release upload $ReleaseTag $asset --repo $Repository --clobber
    } else {
        Invoke-Gh release create $ReleaseTag $asset --repo $Repository --title "NetEase Playlist Backup $ReleaseTag" --generate-notes
    }
}

Write-Host "Published: https://github.com/$Repository" -ForegroundColor Green
