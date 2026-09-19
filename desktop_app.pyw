import argparse

from netease_playlist_backup import gui

if __name__ == "__main__":
    gui(argparse.Namespace(
        playlist=None,
        output="./music-backup",
        api="http://127.0.0.1:3000",
        level="exhigh",
        bitrate="128k",
        ffmpeg="ffmpeg",
        gui=True,
    ))
