$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r .\requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "NetEasePlaylistBackup" ".\desktop_app.pyw"
Write-Host "Built dist\NetEasePlaylistBackup.exe"
