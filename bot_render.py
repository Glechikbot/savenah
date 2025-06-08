import os
import tempfile
import logging
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.utils import executor
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
TT_COOKIES = os.getenv("TT_COOKIES", "")

# Logging
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: Message):
    await message.reply("Привіт! Надішліть лінк на Instagram чи TikTok — я закачаю всі відео 🎬")

@dp.message_handler()
async def handle_message(message: Message):
    url = message.text.strip()
    # Instagram via login
    if 'instagram.com' in url or 'instagr.am' in url:
        if not IG_USERNAME or not IG_PASSWORD:
            await message.reply("🚫 Встановіть логін/пароль Instagram у .env")
            return
        await message.reply("🔍 Завантажую Instagram відео (логін)…")
        with tempfile.TemporaryDirectory() as tmp:
            opts = {
                'format': 'mp4',
                'outtmpl': os.path.join(tmp, '%(id)s.%(ext)s'),
                'quiet': True,
                'username': IG_USERNAME,
                'password': IG_PASSWORD,
            }
            try:
                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    for e in info.get('entries') or [info]:
                        path = ydl.prepare_filename(e)
                        await message.reply_video(open(path, 'rb'))
            except Exception as e:
                logging.exception("Instagram download failed")
                await message.reply(f"🥲 Не вдалося завантажити Instagram:\n{e}")
    # TikTok via cookies header
    elif 'tiktok.com' in url or 'vm.tiktok.com' in url:
        await message.reply("🔍 Завантажую TikTok відео…")
        with tempfile.TemporaryDirectory() as tmp:
            opts = {
                'format': 'mp4',
                'outtmpl': os.path.join(tmp, '%(id)s.%(ext)s'),
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
                await message.reply(f"🥲 Не вдалося завантажити TikTok:\n{e}")
    else:
        await message.reply("❗ Надішліть прямий лінк на Instagram чи TikTok.")

# Health-check
app = Flask(__name__)
@app.route('/', methods=['GET'])
def health(): return 'OK', 200

def run_flask():
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)