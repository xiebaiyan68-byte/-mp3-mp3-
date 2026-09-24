# NetEase Playlist Backup

Windows desktop app and Python CLI for backing up NetEase Cloud Music playlists that the signed-in account can play, then converting them to legacy-compatible MP3 files.

## Features

- Parse a playlist URL or ID through the open-source `NeteaseCloudMusicApi` service.
- QR-code login support; the app sends only the account's own session cookie to the local API.
- Prefer available MP3 sources, then fall back to lossless sources when exposed by the API.
- Select the NetEase source quality: standard, higher, exhigh, lossless, Hi-Res, surround, Dolby, or Master when the signed-in API account exposes it.
- Convert with ffmpeg `libmp3lame`, CBR output from 32 kbps through 320 kbps, 44.1 kHz stereo, ID3v2.3 metadata and album art.
- Save as `Artist - Title.mp3`, skip existing files, and write `backup.log`.

The project does not bypass DRM, paid access, regional restrictions, or other playback controls. It only backs up content the signed-in account can play. Input is restricted to explicit playlist URLs; single-song URLs and bare song IDs are rejected.

## Quick start on Windows

Requirements: Python 3.10+, Node.js 18+, and ffmpeg in `PATH`.

```powershell
python -m pip install -r requirements.txt
.\start_desktop.ps1
```

The first run installs `NeteaseCloudMusicApi` into `api-host\node_modules`. The app opens at `http://127.0.0.1:3000` locally and then shows the desktop UI. Click **扫码登录**, scan with the NetEase Cloud Music app, paste a playlist URL, choose an output folder, and start.

For CLI mode:

```powershell
.\run_backup.ps1 -Playlist "https://music.163.com/playlist?id=123456789" -Output ".\music-backup"
```

## Build an exe

```powershell
.\build_windows.ps1
```

The executable is created at `dist\NetEasePlaylistBackup.exe`. `START_APP.cmd` starts the local API and the desktop app.

## Publish to GitHub

Install and sign in to GitHub CLI once:

```powershell
winget install --id GitHub.cli --exact
gh auth login
```

Then publish the public repository and Windows release (replace `YOUR_NAME/YOUR_REPO`):

```powershell
.\publish_github.ps1 -Repository "YOUR_NAME/YOUR_REPO"
```

Use `-CreatePrivate` for a private repository. The script pushes the `main` branch and uploads `NetEasePlaylistBackup-v1.0.0-windows.zip` as a GitHub Release asset.

## License

MIT. The project depends on the separately licensed `NeteaseCloudMusicApi` package and ffmpeg. Review their licenses before redistribution.
