
import os
import subprocess
import glob
import logging
import re
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Бот-токен
BOT_TOKEN = '7674934548:AAGqw4sur9_gw9HPhjuKBtEzu1huBW4_EfE'

# Директорія для збереження відео
DOWNLOAD_DIR = 'downloads'

# Функція для завантаження відео через yt-dlp
def download_video(url: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_template = os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s')
    cmd = [
        'yt-dlp',
        '--no-playlist',
        '-f', 'mp4',
        '-o', output_template,
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    files = glob.glob(os.path.join(DOWNLOAD_DIR, '*.mp4'))
    if not files:
        raise FileNotFoundError('Не знайдено файлу після завантаження')
    return max(files, key=os.path.getctime)

# Обробник команди /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Привіт! Просто надішли мені посилання на TikTok-видео, і я його завантажу.'
    )

# Загальна логіка завантаження та відправки відео
def handle_download(update: Update, context: CallbackContext, url: str):
    try:
        video_path = download_video(url)
        with open(video_path, 'rb') as video:
            update.message.reply_video(video)
        # os.remove(video_path)  # якщо хочемо видаляти після відправки
    except Exception as e:
        logger.error('Error downloading video: %s', e)
        update.message.reply_text(f'Не вдалося завантажити відео:\n{e}')

# Обробник команди /download
def cmd_download(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text('Надішліть посилання після команди: /download <URL>')
        return
    handle_download(update, context, context.args[0])

# Обробник будь-якого повідомлення з TikTok посиланням
def msg_handler(update: Update, context: CallbackContext):
    text = update.message.text or ''
    # Шукаємо перше TikTok-посилання
    match = re.search(r'https?://(?:www\.)?tiktok\.com/[\w\-/]+|https?://vm\.tiktok\.com/[\w\-/]+', text)
    if match:
        handle_download(update, context, match.group(0))

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('download', cmd_download))
    dp.add_handler(MessageHandler(Filters.text & Filters.regex(r'https?://(?:www\.)?tiktok\.com/|https?://vm\.tiktok\.com/'), msg_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
