#!/usr/bin/env python3
"""Ultra Max Quality YouTube Downloader - simple desktop app.

A small window: paste a YouTube link, pick a folder, click Download. The video
is fetched at the highest available quality (best video + best audio, merged
into one MP4).

This file runs both:
  * from source  ->  python youtube_gui.py   (needs `pip install -r requirements.txt`)
  * as a bundled .exe built by the GitHub Actions workflow (ffmpeg included).
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import yt_dlp
except ImportError:
    # Friendly message instead of a traceback if deps aren't installed.
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing dependency",
        "yt-dlp is not installed.\n\nRun this first in a terminal:\n\n"
        "    pip install -r requirements.txt",
    )
    sys.exit(1)


APP_TITLE = "Ultra Max Quality YouTube Downloader"

# Browsers yt-dlp can read sign-in cookies from, tried in this order in "Auto"
# mode. Cookies let us get past YouTube's "confirm you're not a bot" checks
# when the user is logged into YouTube in that browser.
COMMON_BROWSERS = ["chrome", "edge", "brave", "firefox", "opera", "vivaldi", "chromium"]
BROWSER_CHOICES = ["Auto", "Chrome", "Edge", "Firefox", "Brave", "Opera", "None"]


def resource_path(relative: str) -> str:
    """Resolve a path that works both from source and from a PyInstaller bundle."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def find_ffmpeg_dir() -> str | None:
    """Return the folder containing a bundled ffmpeg, if one ships with the app.

    When packaged as an .exe, ffmpeg.exe sits next to the script inside the
    bundle. When running from source we return None and let yt-dlp find ffmpeg
    on the system PATH.
    """
    candidate = resource_path("ffmpeg.exe")
    if os.path.exists(candidate):
        return os.path.dirname(candidate)
    candidate = resource_path("ffmpeg")
    if os.path.exists(candidate):
        return os.path.dirname(candidate)
    return None


def default_download_dir() -> str:
    downloads = Path.home() / "Downloads"
    return str(downloads if downloads.exists() else Path.home())


class DownloaderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.queue: queue.Queue = queue.Queue()
        self.ffmpeg_dir = find_ffmpeg_dir()
        self._build_ui()
        self.root.after(100, self._poll_queue)

    # ----- UI ---------------------------------------------------------------
    def _build_ui(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("560x300")
        self.root.minsize(520, 300)

        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self.root, padding=14)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text="YouTube link:").grid(row=0, column=0, sticky="w")
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(frm, textvariable=self.url_var)
        url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        url_entry.focus()

        # Save-to folder row
        ttk.Label(frm, text="Save to:").grid(row=2, column=0, sticky="w")
        folder_row = ttk.Frame(frm)
        folder_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        folder_row.columnconfigure(0, weight=1)
        self.folder_var = tk.StringVar(value=default_download_dir())
        ttk.Entry(folder_row, textvariable=self.folder_var).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(folder_row, text="Browse…", command=self._browse).grid(
            row=0, column=1, padx=(8, 0)
        )

        # Options row: audio-only + which browser's sign-in cookies to use.
        opts_row = ttk.Frame(frm)
        opts_row.grid(row=4, column=0, columnspan=2, sticky="w")
        self.audio_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_row, text="Audio only (MP3)", variable=self.audio_only_var
        ).pack(side="left")
        ttk.Label(opts_row, text="     Sign-in cookies from:").pack(side="left")
        self.browser_var = tk.StringVar(value="Auto")
        ttk.Combobox(
            opts_row,
            textvariable=self.browser_var,
            values=BROWSER_CHOICES,
            width=9,
            state="readonly",
        ).pack(side="left", padx=(4, 0))

        # Download button
        self.download_btn = ttk.Button(
            frm, text="⬇  Download", command=self._on_download
        )
        self.download_btn.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 6))

        # Progress + status
        self.progress = ttk.Progressbar(frm, mode="determinate", maximum=100)
        self.progress.grid(row=6, column=0, columnspan=2, sticky="ew")
        self.status_var = tk.StringVar(value="Paste a link and click Download.")
        ttk.Label(frm, textvariable=self.status_var, foreground="#555").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

    def _browse(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.folder_var.get() or os.getcwd())
        if chosen:
            self.folder_var.set(chosen)

    # ----- Download ---------------------------------------------------------
    def _on_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning(APP_TITLE, "Please paste a YouTube link first.")
            return
        folder = self.folder_var.get().strip() or default_download_dir()

        self.download_btn.config(state="disabled")
        self.progress.config(value=0)
        self.status_var.set("Starting…")

        thread = threading.Thread(
            target=self._worker,
            args=(url, folder, self.audio_only_var.get(), self.browser_var.get()),
            daemon=True,
        )
        thread.start()

    def _base_opts(self, folder: str, audio_only: bool) -> dict:
        outtmpl = os.path.join(folder, "%(title)s [%(id)s].%(ext)s")
        if audio_only:
            opts = {
                "format": "bestaudio/best",
                "outtmpl": outtmpl,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "0",
                    }
                ],
            }
        else:
            opts = {
                "format": "bestvideo*+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": outtmpl,
                "concurrent_fragment_downloads": 4,
                "postprocessors": [
                    {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}
                ],
            }
        opts["progress_hooks"] = [self._progress_hook]
        opts["quiet"] = True
        opts["no_warnings"] = True
        if self.ffmpeg_dir:
            opts["ffmpeg_location"] = self.ffmpeg_dir
        return opts

    def _attempt(self, url: str, folder: str, audio_only: bool, browser: str | None) -> None:
        """One download attempt. Raises yt_dlp.utils.DownloadError on failure."""
        opts = self._base_opts(folder, audio_only)
        if browser:
            opts["cookiesfrombrowser"] = (browser,)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    @staticmethod
    def _looks_like_bot_block(err: str) -> bool:
        err = err.lower()
        return any(
            s in err
            for s in ("sign in to confirm", "not a bot", "cookie", "login required")
        )

    def _worker(self, url: str, folder: str, audio_only: bool, browser_choice: str) -> None:
        try:
            Path(folder).mkdir(parents=True, exist_ok=True)

            # Decide which cookie sources to try, in order.
            if browser_choice == "None":
                attempts: list[str | None] = [None]
            elif browser_choice == "Auto":
                # Try without cookies first (fast, works for most videos), then
                # fall back to each installed browser's sign-in cookies.
                attempts = [None] + COMMON_BROWSERS
            else:
                attempts = [browser_choice.lower()]

            last_err = "Unknown error."
            for browser in attempts:
                if browser:
                    self.queue.put(
                        ("status", f"Retrying with {browser.title()} sign-in cookies…")
                    )
                try:
                    self._attempt(url, folder, audio_only, browser)
                    self.queue.put(("done", True, folder))
                    return
                except Exception as exc:  # noqa: BLE001
                    last_err = str(exc)
                    # In Auto mode, only keep trying browsers if this looks like a
                    # bot/sign-in block (or a browser whose cookies we couldn't
                    # read). For anything else (bad URL, etc.), stop now.
                    if browser_choice == "Auto":
                        msg = last_err.lower()
                        keep_going = (
                            self._looks_like_bot_block(last_err)
                            or "could not" in msg  # cookies not found for that browser
                            or "unable to" in msg
                        )
                        if not keep_going:
                            break
                        continue

            self.queue.put(("done", False, last_err))
        except Exception as exc:  # noqa: BLE001
            self.queue.put(("done", False, str(exc)))

    def _progress_hook(self, d: dict) -> None:
        # Runs in the worker thread; just push data to the queue.
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0
            speed = d.get("speed")
            speed_txt = f" • {speed / 1_048_576:.1f} MB/s" if speed else ""
            self.queue.put(("progress", percent, f"Downloading… {percent:.0f}%{speed_txt}"))
        elif status == "finished":
            self.queue.put(("progress", 100, "Merging video and audio…"))

    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self.queue.get_nowait()
                kind = msg[0]
                if kind == "status":
                    self.status_var.set(msg[1])
                elif kind == "progress":
                    _, percent, text = msg
                    self.progress.config(value=percent)
                    self.status_var.set(text)
                elif kind == "done":
                    _, ok, info = msg
                    self.download_btn.config(state="normal")
                    if ok:
                        self.progress.config(value=100)
                        self.status_var.set("✅ Done! Saved to your folder.")
                        messagebox.showinfo(
                            APP_TITLE, f"Download complete!\n\nSaved to:\n{info}"
                        )
                    else:
                        self.progress.config(value=0)
                        if self._looks_like_bot_block(info):
                            self.status_var.set("❌ YouTube asked to confirm you're not a bot.")
                            messagebox.showerror(
                                APP_TITLE,
                                "YouTube blocked this download with a "
                                "\"confirm you're not a bot\" check.\n\n"
                                "How to fix it:\n"
                                "1. Open your normal web browser (Chrome, Edge, "
                                "or Firefox) and make sure you're SIGNED IN to "
                                "youtube.com.\n"
                                "2. Set \"Sign-in cookies from\" to that browser "
                                "(or leave it on Auto).\n"
                                "3. If it still fails, fully CLOSE that browser "
                                "and try again — Chrome/Edge lock their cookies "
                                "while open.\n",
                            )
                        else:
                            self.status_var.set("❌ Something went wrong.")
                            messagebox.showerror(
                                APP_TITLE,
                                "Could not download that video.\n\n"
                                f"Details:\n{info}",
                            )
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)


def main() -> None:
    root = tk.Tk()
    DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
