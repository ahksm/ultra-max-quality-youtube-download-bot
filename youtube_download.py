#!/usr/bin/env python3
"""Ultra Max Quality YouTube Downloader.

A tiny command-line tool that downloads YouTube videos at the highest
available quality (best video + best audio, merged into a single MP4 with
ffmpeg).

Usage:
    python youtube_download.py                         # interactive prompt
    python youtube_download.py <url> [<url> ...]       # one or more links
    python youtube_download.py <url> -o ~/Videos       # custom output folder
    python youtube_download.py <url> --audio-only      # extract MP3 audio only

Run with -h/--help for all options.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit(
        "yt-dlp is not installed.\n"
        "Install the requirements first:\n\n"
        "    pip install -r requirements.txt\n"
    )


def ffmpeg_available() -> bool:
    """ffmpeg is required to merge separate video/audio streams."""
    return shutil.which("ffmpeg") is not None


def build_options(output_dir: Path, audio_only: bool) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(output_dir / "%(title)s [%(id)s].%(ext)s")

    if audio_only:
        return {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",  # best
                }
            ],
            "ignoreerrors": True,
        }

    # bestvideo+bestaudio = the true maximum quality (two separate streams
    # that ffmpeg merges); fall back to the best single progressive stream.
    return {
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "concurrent_fragment_downloads": 4,
        "postprocessors": [
            {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
        ],
        "ignoreerrors": True,
    }


def download(urls: list[str], output_dir: Path, audio_only: bool) -> int:
    opts = build_options(output_dir, audio_only)
    failures = 0
    with yt_dlp.YoutubeDL(opts) as ydl:
        for url in urls:
            print(f"\n=== Downloading: {url} ===")
            try:
                code = ydl.download([url])
                if code != 0:
                    failures += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  ! Failed: {exc}")
                failures += 1
    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download YouTube videos at maximum quality.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python youtube_download.py https://youtu.be/dQw4w9WgXcQ\n"
            "  python youtube_download.py URL1 URL2 -o ~/Videos\n"
            "  python youtube_download.py URL --audio-only\n"
        ),
    )
    parser.add_argument("urls", nargs="*", help="One or more YouTube URLs.")
    parser.add_argument(
        "-o",
        "--output",
        default="downloads",
        help="Folder to save into (default: ./downloads).",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download audio only and save as MP3.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if not ffmpeg_available():
        print(
            "WARNING: ffmpeg was not found on your PATH.\n"
            "Max-quality downloads need ffmpeg to merge video + audio.\n"
            "  - Windows:  download from https://ffmpeg.org/download.html\n"
            "  - macOS:    brew install ffmpeg\n"
            "  - Linux:    sudo apt install ffmpeg\n",
            file=sys.stderr,
        )

    urls = args.urls
    if not urls:
        try:
            entered = input("Paste a YouTube URL (or several, space-separated): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1
        urls = entered.split()

    if not urls:
        print("No URL provided. Nothing to do.")
        return 1

    output_dir = Path(args.output).expanduser()
    failures = download(urls, output_dir, args.audio_only)

    total = len(urls)
    ok = total - failures
    print(f"\nDone. {ok}/{total} succeeded. Files are in: {output_dir.resolve()}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
