# Ultra Max Quality YouTube Downloader

A dead-simple script that downloads YouTube videos at the **highest available
quality** (best video + best audio, merged into one MP4). Runs on your own PC —
Windows, macOS, or Linux.

## What you need (once)

1. **Python 3.8+** — install from [python.org](https://www.python.org/downloads/).
   On Windows, tick **"Add Python to PATH"** during install.
2. **ffmpeg** — needed to merge the video and audio into one file:
   - **Windows:** download from [ffmpeg.org](https://ffmpeg.org/download.html) (or run `winget install ffmpeg`)
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg`

## Get the code

```bash
git clone https://github.com/ahksm/ultra-max-quality-youtube-download-bot.git
cd ultra-max-quality-youtube-download-bot
```

(Or click the green **Code** button on GitHub → **Download ZIP** → unzip it.)

## Easiest way to run

The launcher scripts set everything up automatically (virtual environment +
dependencies) the first time, then run the downloader.

### Windows
Double-click **`run.bat`**, or from a terminal:
```bat
run.bat https://youtu.be/VIDEO_ID
```

### macOS / Linux
```bash
./run.sh https://youtu.be/VIDEO_ID
```
(First time only: `chmod +x run.sh` to make it executable.)

Run it with **no URL** and it will simply ask you to paste one.

Your videos are saved to the **`downloads/`** folder.

## Manual way (if you prefer)

```bash
pip install -r requirements.txt
python youtube_download.py https://youtu.be/VIDEO_ID
```

## Options

```text
python youtube_download.py [URLs...] [options]

  URLs                  One or more YouTube links (any mix of watch / youtu.be /
                        shorts / playlist links). If omitted, you'll be prompted.

  -o, --output FOLDER   Where to save files (default: ./downloads)
  --audio-only          Download audio only, saved as MP3
  -h, --help            Show all options
```

### Examples
```bash
# Single video at max quality
python youtube_download.py https://youtu.be/dQw4w9WgXcQ

# Several at once, into a custom folder
python youtube_download.py URL1 URL2 -o ~/Videos

# Just the audio as MP3
python youtube_download.py URL --audio-only
```

## Troubleshooting

- **"ffmpeg was not found"** — install ffmpeg (see above) and reopen your terminal.
- **`HTTP Error 403` / "Sign in to confirm you're not a bot"** — YouTube
  sometimes blocks downloads from data-center IPs or rate-limits you. This works
  fine from a normal home connection. If it persists, update yt-dlp
  (`pip install -U yt-dlp`).
- **Slow or stuck** — very high-resolution videos (4K/8K) are large; give it time.

## Legal

Only download content you have the right to download. Respect YouTube's Terms of
Service and applicable copyright law.
