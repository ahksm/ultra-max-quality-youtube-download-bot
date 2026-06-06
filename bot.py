"""Ultra Max Quality YouTube Download Bot.

A Telegram bot that downloads YouTube videos at the highest available quality
using yt-dlp and sends them back to the user.

Configuration is read from environment variables:
    BOT_TOKEN            (required) Telegram bot token from @BotFather.
    MAX_UPLOAD_MB        (optional) Max file size to upload, in MB. Defaults to
                         50 (the standard Bot API limit). Raise this only if you
                         run against a local Bot API server that allows larger
                         uploads (up to ~2000).
    DOWNLOAD_DIR         (optional) Where to store temporary downloads.
    TELEGRAM_API_BASE    (optional) Base URL of a local Bot API server, e.g.
                         http://localhost:8081/bot for >50MB uploads.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
import uuid
from pathlib import Path

import yt_dlp
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("yt-bot")
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
DOWNLOAD_DIR = Path(os.environ.get("DOWNLOAD_DIR", tempfile.gettempdir())) / "yt_bot"
TELEGRAM_API_BASE = os.environ.get("TELEGRAM_API_BASE", "").strip()

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Matches the bulk of YouTube URL shapes (youtube.com/watch, youtu.be, shorts,
# live, embed, playlists). We keep it permissive and let yt-dlp do real parsing.
YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?|shorts/|live/|embed/|playlist\?)|youtu\.be/)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Download helpers (run in a worker thread; yt-dlp is blocking)
# ---------------------------------------------------------------------------


def _format_size(num_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} GB"


def _probe(url: str) -> dict:
    """Fetch metadata without downloading."""
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)


def _download(url: str, dest_dir: Path) -> Path:
    """Download the best video+audio and merge into a single MP4.

    Returns the path to the finished file. Raises on failure.
    """
    out_template = str(dest_dir / "%(title).80s [%(id)s].%(ext)s")
    ydl_opts = {
        # bestvideo+bestaudio gives the true max quality (separate streams that
        # we merge); fall back to the best progressive stream if merge isn't
        # possible.
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "restrictfilenames": False,
        "concurrent_fragment_downloads": 4,
        # Re-encode-free remux to mp4 when streams are compatible.
        "postprocessors": [
            {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Resolve the actual output filename after post-processing.
        filename = ydl.prepare_filename(info)
        path = Path(filename)
        if path.suffix.lower() != ".mp4":
            mp4 = path.with_suffix(".mp4")
            if mp4.exists():
                path = mp4
        if not path.exists():
            # Last resort: pick the most recently modified file in the dir.
            candidates = sorted(dest_dir.glob("*"), key=lambda p: p.stat().st_mtime)
            if not candidates:
                raise FileNotFoundError("Download produced no file.")
            path = candidates[-1]
    return path


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

WELCOME = (
    "🎬 *Ultra Max Quality YouTube Downloader*\n\n"
    "Send me a YouTube link and I'll fetch it at the highest available "
    "quality and send it back to you.\n\n"
    f"⚠️ Telegram caps bot uploads at *{MAX_UPLOAD_MB} MB*. Larger videos "
    "can't be delivered through the bot.\n\n"
    "Just paste a link to begin!"
)


async def cmd_start(update: Update, context) -> None:
    await update.message.reply_markdown(WELCOME)


async def cmd_help(update: Update, context) -> None:
    await update.message.reply_markdown(WELCOME)


async def handle_link(update: Update, context) -> None:
    message = update.message
    text = (message.text or "").strip()
    match = YOUTUBE_RE.search(text)
    if not match:
        await message.reply_text(
            "That doesn't look like a YouTube link. Send me a "
            "youtube.com or youtu.be URL."
        )
        return

    url = text[match.start():].split()[0]
    status = await message.reply_text("🔎 Looking up the video…")

    try:
        info = await asyncio.to_thread(_probe, url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Probe failed for %s: %s", url, exc)
        await status.edit_text("❌ Couldn't read that video. Is the link valid and public?")
        return

    title = info.get("title", "video")
    duration = info.get("duration")
    dur_str = ""
    if duration:
        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)
        dur_str = f" • {h}:{m:02d}:{s:02d}" if h else f" • {m}:{s:02d}"

    await status.edit_text(f"⬇️ Downloading *{title}*{dur_str} at max quality…",
                           parse_mode="Markdown")
    await context.bot.send_chat_action(message.chat_id, ChatAction.UPLOAD_VIDEO)

    job_dir = DOWNLOAD_DIR / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        path = await asyncio.to_thread(_download, url, job_dir)
        size = path.stat().st_size

        if size > MAX_UPLOAD_BYTES:
            await status.edit_text(
                f"⚠️ *{title}* downloaded fine ({_format_size(size)}), but that's "
                f"larger than the {MAX_UPLOAD_MB} MB upload limit, so I can't send "
                "it through Telegram.\n\n"
                "Tip: run this bot against a local Bot API server to lift the limit.",
                parse_mode="Markdown",
            )
            return

        await status.edit_text(f"📤 Uploading *{title}* ({_format_size(size)})…",
                               parse_mode="Markdown")

        with path.open("rb") as fh:
            await context.bot.send_video(
                chat_id=message.chat_id,
                video=fh,
                caption=title,
                supports_streaming=True,
                duration=duration,
                read_timeout=600,
                write_timeout=600,
                connect_timeout=60,
            )
        await status.delete()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Download/upload failed for %s", url)
        await status.edit_text(f"❌ Something went wrong: {exc}")
    finally:
        # Clean up the whole job directory.
        for f in job_dir.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            job_dir.rmdir()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN is not set. Export it (or put it in a .env file) before "
            "starting the bot. See README.md."
        )

    builder = Application.builder().token(BOT_TOKEN)
    if TELEGRAM_API_BASE:
        builder = builder.base_url(TELEGRAM_API_BASE)
    app = builder.build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    logger.info("Bot is up. Max upload: %s MB. Download dir: %s",
                MAX_UPLOAD_MB, DOWNLOAD_DIR)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
