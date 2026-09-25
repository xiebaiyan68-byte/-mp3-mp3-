# 网易云音乐歌单/单曲 MP3 备份工具

把网易云音乐中**当前账号可以正常播放的歌单或单曲**，备份为带标题、歌手、专辑和封面的 MP3 文件。支持选择网易云可用音质和 MP3 码率，适合个人本地整理、转存到老 MP3 播放器或车载设备。

这是一个 Windows 桌面工具，也提供 PowerShell 和 Python 命令行入口。输入网易云歌单链接（例如 `https://music.163.com/playlist?id=123456789`）或单曲链接，扫码登录后即可开始。

Windows desktop app and Python CLI for backing up playable NetEase Cloud Music playlists or songs, then converting them to compatible MP3 files.

## Features

- Parse a playlist URL/ID or a single-song URL/ID through the open-source `NeteaseCloudMusicApi` service.
- QR-code login support; the app sends only the account's own session cookie to the local API.
- Prefer available MP3 sources, then fall back to lossless sources when exposed by the API.
- Select the NetEase source quality: standard, higher, exhigh, lossless, Hi-Res, surround, Dolby, or Master when the signed-in API account exposes it.
- Convert with ffmpeg `libmp3lame`, CBR output from 32 kbps through 320 kbps, 44.1 kHz stereo, ID3v2.3 metadata and album art.
- Save as `Artist - Title.mp3`, skip existing files, and write `backup.log`.

## 你可以用它做什么

- 解析网易云歌单中的全部歌曲，或只处理一首单曲。
- 优先使用账号能获取的 MP3 音源；没有 MP3 时使用可获取的 FLAC/WAV，再由 ffmpeg 转成 MP3。
- 选择标准、较高、极高、无损、Hi-Res、环绕声、杜比、臻品等账号实际可用的音质。
- 选择 32、40、48、56、64、80、96、112、128、160、192、224、256 或 320 kbps CBR MP3。
- 使用 44.1 kHz、立体声、`libmp3lame` 编码，并保留 ID3 标签和专辑封面。

## 使用前请知道

程序不会绕过 VIP、DRM、地区限制或任何付费权限。歌曲只有在登录账号本身可以正常播放、且用户有权进行本地备份时才会处理；不可获取的歌曲会记录到日志并跳过。

歌单链接和单曲链接都支持；程序会根据链接类型自动判断输入内容。

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
