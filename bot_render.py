
import os
import tempfile
import logging
import threading
from datetime import datetime, timedelta
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.utils import executor
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

TT_COOKIES = os.getenv("TT_COOKIES", "")
IG_COOKIES = os.getenv("IG_COOKIES", "")

# If IG_COOKIES present, write Netscape-format cookiefile
COOKIEFILE = 'instagram_cookies.txt'
if IG_COOKIES:
    expiry = int((datetime.now() + timedelta(days=365)).timestamp())
    lines = ["# Netscape HTTP Cookie File"]
    for part in IG_COOKIES.strip('"').split(';'):
        name, value = part.strip().split('=', 1)
        lines.append(f".instagram.com	TRUE	/ 	FALSE	{expiry}	{name}	{value}")
    with open(COOKIEFILE, 'w') as f:
        f.write("\n".join(lines))

# Logging setup
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: Message):
    await message.reply("Привіт! Надішліть лінк на Instagram чи TikTok — я закачаю всі відео 🎬")

@dp.message_handler()
async def handle_message(message: Message):
    url = message.text.strip()
    # Instagram
    if 'instagram.com' in url or 'instagr.am' in url:
        await message.reply("🔍 Завантажую Instagram відео…")
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = {
                'format': 'mp4',
                'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
                'quiet': True,
                'cookiefile': COOKIEFILE if IG_COOKIES else None,
            }
            # Remove None entries
            opts = {k: v for k, v in opts.items() if v is not None}
            try:
                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    entries = info.get('entries') or [info]
                    for entry in entries:
                        path = ydl.prepare_filename(entry)
                        await message.reply_video(open(path, 'rb'))
            except Exception as e:
                logging.exception("Instagram download failed")
                await message.reply(f"🥲 Не вдалося завантажити Instagram: {e}")

    # TikTok
    elif 'tiktok.com' in url or 'vm.tiktok.com' in url:
        await message.reply("🔍 Завантажую TikTok відео…")
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = {
                'format': 'mp4',
                'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
                'quiet': True,
            }
            if TT_COOKIES:
                opts['http_headers'] = {'Cookie': TT_COOKIES}
            try:
                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    path = ydl.prepare_filename(info)
                    await message.reply_video(open(path, 'rb'))
            except Exception as e:
                logging.exception("TikTok download failed")
                await message.reply(f"🥲 Не вдалося завантажити TikTok: {e}")
    else:
        await message.reply("❗ Надішліть прямий лінк на Instagram чи TikTok.")

# Health-check server
flask_app = Flask(__name__)

@flask_app.route('/', methods=['GET'])
def health():
    return 'OK', 200

def run_flask():
    port = int(os.getenv('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)
