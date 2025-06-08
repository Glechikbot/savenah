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

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
TT_COOKIES = os.getenv("TT_COOKIES", "")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start','help'])
async def start(m: Message):
    await m.reply("Привіт! Скидайте посилання на Instagram/TikTok — качаю відео.")

@dp.message_handler()
async def handler(m: Message):
    url = m.text.strip()
    if 'instagram.com' in url or 'instagr.am' in url:
        await m.reply("🔍 Завантажую Instagram (cookies-from-browser)…")
        with tempfile.TemporaryDirectory() as tmp:
            opts = {
                'format': 'mp4',
                'outtmpl': os.path.join(tmp, '%(id)s.%(ext)s'),
                'quiet': True,
                # ось ключове:
                'cookies_from_browser': 'chrome'
            }
            try:
                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    for e in info.get('entries') or [info]:
                        p = ydl.prepare_filename(e)
                        await m.reply_video(open(p,'rb'))
            except Exception as e:
                logging.exception("IG failed")
                await m.reply(f"🥲 Не вдалось взяти Instagram:\n{e}")
    elif 'tiktok.com' in url or 'vm.tiktok.com' in url:
        await m.reply("🔍 Завантажую TikTok…")
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
                    p = ydl.prepare_filename(info)
                    await m.reply_video(open(p,'rb'))
            except Exception as e:
                logging.exception("TT failed")
                await m.reply(f"🥲 Не вдалось взяти TikTok:\n{e}")
    else:
        await m.reply("❗ Надішли прямий лінк на Instagram або TikTok.")

app = Flask(__name__)
@app.route('/', methods=['GET'])
def health(): return "OK", 200

def run():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT',10000)))

if __name__=='__main__':
    threading.Thread(target=run, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)
