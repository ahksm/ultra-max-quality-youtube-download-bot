# Ultra Max Quality YouTube Downloader

Download YouTube videos at the **highest available quality** (best video + best
audio, merged into one MP4).

---

## 🟢 Just want to use it? (Windows — no setup, recommended)

No Python, no ffmpeg, no terminal. One file.

1. **[⬇ Download YouTube-Max-Downloader.exe](https://github.com/ahksm/ultra-max-quality-youtube-download-bot/releases/download/latest/YouTube-Max-Downloader.exe)**
   (or browse the [Releases page](https://github.com/ahksm/ultra-max-quality-youtube-download-bot/releases/tag/latest) and grab it under **Assets**).
2. **Double-click it.** A small window opens.
3. Paste a YouTube link, click **Download**. Done — the video lands in your
   **Downloads** folder.

> **First time you run it, Windows may say "Windows protected your PC."**
> That's just because the app isn't code-signed. Click **More info → Run anyway**.
> It's safe — the app is built automatically from this repository's source code.

That's the whole thing. The rest of this page is for people who want to run it
from source or build it themselves.

---

## How the .exe gets built

A [GitHub Actions workflow](.github/workflows/build-windows.yml) builds the
Windows app automatically (bundling Python **and** ffmpeg inside a single file)
and publishes it to the Releases page. To trigger a build: push a change, or go
to the repo's **Actions** tab → **Build Windows App** → **Run workflow**.

---

## Run from source (any OS)

Needs **Python 3.8+** and **ffmpeg** installed.

```bash
git clone https://github.com/ahksm/ultra-max-quality-youtube-download-bot.git
cd ultra-max-quality-youtube-download-bot
pip install -r requirements.txt
```

Install ffmpeg:
- **Windows:** `winget install ffmpeg` (or [ffmpeg.org](https://ffmpeg.org/download.html))
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### The window (GUI)
```bash
python youtube_gui.py
```

### Or the command line
```bash
python youtube_download.py https://youtu.be/VIDEO_ID
python youtube_download.py URL1 URL2 -o ~/Videos   # several, custom folder
python youtube_download.py URL --audio-only        # MP3 audio only
```

### One-click launcher scripts
- **Windows:** double-click **`run.bat`**
- **macOS/Linux:** `./run.sh`

These auto-create a virtual environment and install dependencies on first run.

---

## Troubleshooting

- **"Windows protected your PC"** — click **More info → Run anyway** (unsigned app).
- **"Sign in to confirm you're not a bot"** — YouTube wants you logged in.
  The app handles this with the **"Sign-in cookies from"** dropdown:
  1. In your normal browser (Chrome/Edge/Firefox), make sure you're **signed in
     to youtube.com**.
  2. Leave the dropdown on **Auto** (it tries your browsers automatically), or
     pick the exact browser you use.
  3. If it still fails, **fully close that browser** and try again — Chrome and
     Edge lock their cookies while open.

  From the command line, use `--cookies-from-browser chrome` (or `edge`,
  `firefox`, `brave`).
- **`HTTP Error 403`** — YouTube can rate-limit certain networks. Works fine
  from a normal home connection; if it persists, grab a fresh build (yt-dlp is
  updated on every build).
- **"ffmpeg was not found"** (source mode only) — install ffmpeg and reopen your
  terminal. The .exe already includes ffmpeg.

## Legal

Only download content you have the right to download. Respect YouTube's Terms of
Service and applicable copyright law.
