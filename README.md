# ultra-max-quality-youtube-download-bot

A Telegram bot that downloads YouTube videos at the **highest available quality**
(true `bestvideo+bestaudio`, merged with ffmpeg) and sends them straight back to
you in chat.

## Features

- 🎬 Downloads the best available video **and** audio stream and merges them to MP4
- 🔗 Accepts `youtube.com/watch`, `youtu.be`, Shorts, Live, and embed links
- 📊 Live status messages (looking up → downloading → uploading)
- 🧹 Cleans up temporary files after every job
- 🛡️ No secrets in the repo — the token is read from the environment
- 📦 Optional support for a local Bot API server to bypass the 50 MB upload cap

## Requirements

- **Python 3.10+**
- **ffmpeg** on your `PATH` (required to merge the separate video/audio streams)
  - Debian/Ubuntu: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: download from <https://ffmpeg.org/download.html>

## Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure your token
cp .env.example .env
#   then edit .env and paste your token from @BotFather

# 3. Run it
python bot.py
```

## Configuration

All configuration is via environment variables (or a `.env` file):

| Variable            | Required | Default       | Description                                              |
| ------------------- | -------- | ------------- | -------------------------------------------------------- |
| `BOT_TOKEN`         | ✅       | —             | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `MAX_UPLOAD_MB`     | ❌       | `50`          | Max file size to upload. Bot API caps this at 50 MB.     |
| `DOWNLOAD_DIR`      | ❌       | system temp   | Where to store temporary downloads.                      |
| `TELEGRAM_API_BASE` | ❌       | —             | Base URL of a local Bot API server for large uploads.    |

## Usage

1. Start a chat with your bot and send `/start`.
2. Paste any YouTube link.
3. The bot downloads it at max quality and sends the video back.

## About the 50 MB limit

Telegram's standard Bot API limits bot uploads to **50 MB**. Many max-quality
videos exceed this. To deliver larger files, run a
[local Bot API server](https://github.com/tdlib/telegram-bot-api) (which allows
uploads up to ~2 GB) and point the bot at it:

```bash
export TELEGRAM_API_BASE="http://localhost:8081/bot"
export MAX_UPLOAD_MB=2000
```

When a download exceeds the limit, the bot tells you instead of failing silently.

## Security note

Never commit your bot token. It belongs in `.env` (which is git-ignored) or your
shell environment. If a token is ever exposed, revoke it in @BotFather with
`/revoke` and generate a new one.

## Legal

Only download content you have the right to download. Respect YouTube's Terms of
Service and applicable copyright law.
