$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r .\requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "NetEasePlaylistBackup" ".\desktop_app.pyw"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed with exit code $LASTEXITCODE" }
Write-Host "Built dist\NetEasePlaylistBackup.exe"
