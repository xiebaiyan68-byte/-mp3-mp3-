# 网易云音乐转mp3（歌单/单曲） 可选音质（原版）和码率（常见）

这是 Windows 便携版。解压后双击 `START_APP.cmd` 即可运行，不需要安装 Python、Node.js 或 ffmpeg。

##

## 使用

1. 解压整个目录，不要只复制 EXE。
2. 双击 `START_APP.cmd`。
3. 在程序中扫码登录，输入网易云歌单链接，选择输出目录和音质后开始备份。

程序会使用本目录内的 `runtime\\node.exe`、`runtime\\ffmpeg.exe` 和 `api-host\\node_modules`。首次启动通常只需要几秒；API 窗口在后台运行。

## 说明

- 仅处理登录账号能够正常播放、且用户有权进行本地备份的内容。
- 不绕过 DRM、付费权限、地区限制或其他访问控制。
- 输出文件默认命名为 `歌手 - 歌名.mp3`，已存在的文件会跳过。
- 日志默认写入 `%APPDATA%\\NetEasePlaylistBackup\\backup.log`。

## 关闭

关闭主程序后，如仍有后台 API 进程，可在任务管理器中结束对应的 `node.exe` 进程。
