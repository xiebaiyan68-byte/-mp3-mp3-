#!/usr/bin/env python3
"""Personal backup/transcode workflow for playable NetEase Cloud Music playlists.

Requires a local NeteaseCloudMusicApi server (default http://127.0.0.1:3000)
and ffmpeg in PATH. This script does not bypass DRM or paid-content controls.
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def config_path() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home())) / "NetEasePlaylistBackup"
    root.mkdir(parents=True, exist_ok=True)
    return root / "settings.json"


def load_cookie() -> str:
    try:
        return str(json.loads(config_path().read_text(encoding="utf-8")).get("cookie", ""))
    except (OSError, ValueError, TypeError):
        return ""


def save_cookie(cookie: str) -> None:
    config_path().write_text(json.dumps({"cookie": cookie}, ensure_ascii=False), encoding="utf-8")


def clean_name(value: str, fallback: str = "未知") -> str:
    value = html.unescape(str(value or fallback)).strip()
    value = INVALID_CHARS.sub("_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return (value or fallback)[:180]


SOURCE_LEVELS = (
    ("standard", "标准 MP3 128k"),
    ("higher", "较高 MP3 192k"),
    ("exhigh", "极高 MP3 320k"),
    ("lossless", "无损 FLAC"),
    ("hires", "Hi-Res 无损"),
    ("jyeffect", "高清环绕"),
    ("sky", "沉浸环绕"),
    ("dolby", "杜比全景声"),
    ("jymaster", "超清母带"),
)
OUTPUT_BITRATES = ("32k", "40k", "48k", "56k", "64k", "80k", "96k", "112k", "128k",
                   "160k", "192k", "224k", "256k", "320k")


def playlist_id(value: str) -> str:
    """Extract an id only from an explicit playlist URL; never accept song URLs/IDs."""
    value = value.strip()
    parsed = urlparse(value)
    query = parse_qs(parsed.query)
    if not query and parsed.fragment:
        query = parse_qs(parsed.fragment.split("?", 1)[-1])
    if parsed.netloc and parsed.netloc not in ("music.163.com", "www.music.163.com"):
        raise ValueError("只支持网易云歌单链接")
    if "/playlist" not in parsed.path and "#/playlist" not in value:
        raise ValueError("只支持歌单链接，不能下载单曲；请粘贴 https://music.163.com/playlist?id=...")
    query_id = query.get("id", [None])[0]
    if query_id and query_id.isdigit():
        return query_id
    raise ValueError("歌单链接缺少有效的 id 参数")


class NeteaseAPI:
    def __init__(self, base: str, session: requests.Session, cookie: str = ""):
        self.base = base.rstrip("/")
        self.session = session
        self.cookie = cookie

    def get(self, path: str, **params: Any) -> dict[str, Any]:
        if self.cookie:
            params.setdefault("cookie", self.cookie)
        response = self.session.get(f"{self.base}{path}", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("code") not in (None, 200):
            raise RuntimeError(f"API 返回错误: {data}")
        return data

    def playlist(self, pid: str) -> list[dict[str, Any]]:
        data = self.get("/playlist/detail", id=pid)
        playlist = data.get("playlist") or {}
        tracks = playlist.get("tracks") or []
        # Some deployments return only partial tracks; hydrate missing IDs.
        if playlist.get("trackIds") and len(tracks) < len(playlist["trackIds"]):
            ids = ",".join(str(x["id"]) for x in playlist["trackIds"])
            detail = self.get("/song/detail", ids=ids)
            tracks = detail.get("songs") or tracks
        return tracks

    def url(self, song_id: int, level: str) -> str | None:
        data = self.get("/song/url/v1", id=song_id, level=level)
        rows = data.get("data") or []
        return rows[0].get("url") if rows else None

    def best_url(self, song_id: int, preferred: str) -> str | None:
        # Try the requested NetEase quality first, then degrade to playable levels.
        levels = [preferred]
        for level in ("jymaster", "hires", "lossless", "dolby", "sky", "jyeffect",
                      "exhigh", "higher", "standard"):
            if level not in levels:
                levels.append(level)
        for level in levels:
            try:
                url = self.url(song_id, level)
            except requests.RequestException:
                continue
            except RuntimeError:
                continue
            if url:
                return url
        return None


def ffmpeg_convert(source: Path, target: Path, title: str, artist: str,
                   album: str, cover: Path | None, bitrate: str, ffmpeg: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source)]
    if cover and cover.exists():
        cmd += ["-i", str(cover), "-map", "0:a:0", "-map", "1:v:0", "-c:v", "mjpeg",
                "-disposition:v:0", "attached_pic"]
    else:
        cmd += ["-map", "0:a:0"]
    cmd += ["-c:a", "libmp3lame", "-b:a", bitrate, "-ar", "44100", "-ac", "2",
            "-id3v2_version", "3", "-metadata", f"title={title}",
            "-metadata", f"artist={artist}", "-metadata", f"album={album}", str(target)]
    subprocess.run(cmd, check=True, timeout=300)


def download(url: str, destination: Path, session: requests.Session) -> None:
    with session.get(url, stream=True, timeout=(15, 60)) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    handle.write(chunk)


def process(args: argparse.Namespace) -> int:
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "backup.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()])
    if not shutil.which(args.ffmpeg):
        logging.error("找不到 ffmpeg，请安装并加入 PATH，或用 --ffmpeg 指定路径")
        return 2
    pid = playlist_id(args.playlist)
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=Retry(
        total=3, connect=3, read=3, status=3,
        backoff_factor=0.5, status_forcelist=(502, 503, 504),
        allowed_methods=frozenset(("GET",)),
    )))
    api = NeteaseAPI(args.api, session, getattr(args, "cookie", "") or load_cookie())
    try:
        tracks = api.playlist(pid)
    except Exception as exc:
        logging.error("解析歌单失败: %s", exc)
        return 1
    if not tracks:
        logging.error("歌单没有可见歌曲")
        return 1
    logging.info("歌单 %s: %d 首歌曲", pid, len(tracks))
    with tempfile.TemporaryDirectory(prefix="netease-backup-") as temp_dir:
        temp = Path(temp_dir)
        for index, song in enumerate(tracks, 1):
            song_id = song.get("id")
            title = clean_name(song.get("name"), f"song-{song_id}")
            artists = song.get("ar") or song.get("artists") or []
            artist = clean_name(" & ".join(str(x.get("name", "")) for x in artists), "未知歌手")
            album_obj = song.get("al") or song.get("album") or {}
            album = clean_name(album_obj.get("name"), "未知专辑")
            target = output / f"{clean_name(artist)} - {title}.mp3"
            if target.exists() and target.stat().st_size > 0:
                logging.info("[%d/%d] 跳过已存在: %s", index, len(tracks), target.name)
                continue
            try:
                source_url = api.best_url(int(song_id), args.level)
                if not source_url:
                    logging.warning("[%d/%d] 无可下载音源，跳过: %s - %s", index, len(tracks), artist, title)
                    continue
                suffix = ".flac" if "flac" in source_url.lower() else ".source"
                source = temp / f"{song_id}{suffix}"
                cover = None
                cover_url = album_obj.get("picUrl") or album_obj.get("picUrl")
                if cover_url:
                    cover = temp / f"{song_id}.jpg"
                    try:
                        download(cover_url, cover, session)
                    except requests.RequestException:
                        cover = None
                logging.info("[%d/%d] 下载: %s - %s", index, len(tracks), artist, title)
                download(source_url, source, session)
                ffmpeg_convert(source, target, title, artist, album, cover, args.bitrate, args.ffmpeg)
                logging.info("[%d/%d] 完成: %s", index, len(tracks), target.name)
            except Exception as exc:
                logging.error("[%d/%d] 失败 %s - %s: %s", index, len(tracks), artist, title, exc)
    return 0


def gui(defaults: argparse.Namespace) -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    import threading
    root = tk.Tk(); root.title("网易云歌单 MP3 备份"); root.resizable(False, False)
    root.geometry("700x430")
    defaults.cookie = load_cookie()
    fields: dict[str, tk.StringVar] = {}
    for row, (label, key, value) in enumerate((("歌单链接", "playlist", defaults.playlist or ""), ("API 地址", "api", defaults.api), ("输出目录", "output", defaults.output))):
        ttk.Label(root, text=label).grid(row=row, column=0, padx=12, pady=9, sticky="w")
        var = tk.StringVar(value=value); fields[key] = var
        ttk.Entry(root, textvariable=var, width=58).grid(row=row, column=1, padx=8, pady=9, columnspan=2, sticky="ew")
    ttk.Label(root, text="码率").grid(row=3, column=0, padx=12, pady=9, sticky="w")
    ttk.Label(root, text="网易云音质").grid(row=3, column=0, padx=12, pady=9, sticky="w")
    level = tk.StringVar(value=defaults.level)
    level_values = [f"{key} | {label}" for key, label in SOURCE_LEVELS]
    level_box = ttk.Combobox(root, textvariable=level, values=level_values, state="readonly", width=28)
    level_box.grid(row=3, column=1, padx=8, pady=9, sticky="w")
    level.set(next((x for x in level_values if x.startswith(defaults.level + " |")), level_values[2]))
    ttk.Label(root, text="输出 MP3 码率").grid(row=4, column=0, padx=12, pady=9, sticky="w")
    bitrate = tk.StringVar(value=defaults.bitrate)
    ttk.Combobox(root, textvariable=bitrate, values=OUTPUT_BITRATES, state="readonly", width=10).grid(row=4, column=1, padx=8, pady=9, sticky="w")
    login_status = tk.StringVar(value="已保存登录状态" if defaults.cookie else "未登录：只能获取公开可播放音源")
    status = tk.StringVar(value="就绪")
    ttk.Label(root, textvariable=login_status, foreground="#555").grid(row=5, column=0, columnspan=3, padx=12, pady=5, sticky="w")
    ttk.Label(root, textvariable=status, foreground="#555").grid(row=6, column=0, columnspan=3, padx=12, pady=5, sticky="w")
    choose_button = ttk.Button(root, text="选择目录", command=lambda: fields["output"].set(filedialog.askdirectory() or fields["output"].get()))
    choose_button.grid(row=2, column=3, padx=8)
    def qr_login():
        window = tk.Toplevel(root); window.title("网易云扫码登录"); window.resizable(False, False)
        label = ttk.Label(window, text="正在生成二维码…"); label.pack(padx=24, pady=16)
        qr_label = ttk.Label(window); qr_label.pack(padx=24, pady=8)
        hint = ttk.Label(window, text="请使用网易云音乐 App 扫码并确认"); hint.pack(padx=24, pady=16)
        stopped = threading.Event()
        window.protocol("WM_DELETE_WINDOW", lambda: (stopped.set(), window.destroy()))
        def fail(message: str):
            if window.winfo_exists(): label.configure(text=message)
        def success(cookie: str):
            defaults.cookie = cookie; save_cookie(cookie); login_status.set("已登录，下载将使用当前账号的播放权限")
            if window.winfo_exists(): window.destroy()
            messagebox.showinfo("登录成功", "网易云登录状态已保存")
        def worker():
            try:
                session = requests.Session(); base = fields["api"].get().rstrip("/")
                stamp = str(int(__import__("time").time() * 1000))
                key_data = session.get(f"{base}/login/qr/key", params={"timestamp": stamp}, timeout=15).json()
                key = key_data["data"]["unikey"]
                qr_data = session.get(f"{base}/login/qr/create", params={"key": key, "qrimg": "true", "timestamp": stamp}, timeout=15).json()
                encoded = qr_data["data"]["qrimg"].split(",", 1)[-1]
                def show_qr():
                    image = tk.PhotoImage(data=encoded)
                    qr_label.configure(image=image); qr_label.image = image; label.configure(text="等待扫码")
                root.after(0, show_qr)
                while not stopped.wait(2):
                    stamp = str(int(__import__("time").time() * 1000))
                    data = session.get(f"{base}/login/qr/check", params={"key": key, "timestamp": stamp}, timeout=15).json()
                    code = data.get("code")
                    if code == 802:
                        root.after(0, lambda: label.configure(text="已扫码，请在手机上确认"))
                    elif code == 803 and data.get("cookie"):
                        root.after(0, success, data["cookie"]); return
                    elif code == 800:
                        root.after(0, fail, "二维码已过期，请关闭窗口后重试"); return
            except Exception as exc:
                root.after(0, fail, f"登录失败：{exc}")
        threading.Thread(target=worker, daemon=True).start()
    ttk.Button(root, text="扫码登录", command=qr_login).grid(row=4, column=3, padx=8)
    start_button = ttk.Button(root, text="开始备份")
    start_button.grid(row=7, column=1, pady=14, sticky="w")
    def run():
        for key, var in fields.items(): setattr(defaults, key, var.get())
        defaults.bitrate = bitrate.get(); defaults.level = level.get().split(" |", 1)[0]; defaults.gui = False
        code = process(defaults)
        root.after(0, finished, code)
    def finished(code: int):
        start_button.configure(state="normal"); choose_button.configure(state="normal")
        status.set("处理完成，请查看输出目录中的 backup.log" if code == 0 else "处理失败，请查看日志")
        messagebox.showinfo("网易云歌单备份", status.get())
    def start():
        if not fields["playlist"].get().strip():
            messagebox.showwarning("缺少歌单链接", "请先粘贴网易云歌单链接")
            return
        start_button.configure(state="disabled"); choose_button.configure(state="disabled"); status.set("正在下载和转码，请稍候…")
        threading.Thread(target=run, daemon=True).start()
    start_button.configure(command=start)
    root.mainloop(); return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="网易云歌单个人本地 MP3 备份与转码")
    parser.add_argument("playlist", nargs="?", help="网易云歌单 URL（不接受单曲链接或纯数字 ID）")
    parser.add_argument("-o", "--output", default="./music-backup")
    parser.add_argument("--api", default="http://127.0.0.1:3000")
    parser.add_argument("--level", default="exhigh", choices=tuple(x[0] for x in SOURCE_LEVELS))
    parser.add_argument("--bitrate", default="128k", choices=OUTPUT_BITRATES)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()
    if args.gui:
        return gui(args)
    if not args.playlist:
        parser.error("命令行模式需要提供歌单链接；或使用 --gui")
    return process(args)


if __name__ == "__main__":
    sys.exit(main())
