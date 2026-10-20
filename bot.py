import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from flask import Flask
from threading import Thread
import yt_dlp

API_TOKEN = '8712589651:AAHzVtxiqebxZ8QNzVLULkxYSq_xUjp4IN8'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Start buyrug'i
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Xush kelibsiz!**\n\n"
        "Men orqali siz:\n"
        "1. **Instagram** Reel/Post havolasini yuborib, videoni yuklab olishingiz;\n"
        "2. **Qo'shiq nomi** yoki ijrochi ismini yozib, qo'shiqni topishingiz mumkin.\n\n"
        "Menga shunchaki link yoki qo'shiq nomini yuboring!"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

# Instagram linklarini ushlash
@dp.message(F.text.contains("instagram.com"))
async def download_instagram(message: types.Message):
    status_msg = await message.answer("📥 Instagram video yuklanmoqda, kuting...")
    url = message.text.strip()

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'insta_video.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        
        file_path = await loop.run_in_executor(None, download)
        
        if os.path.exists(file_path):
            video_file = types.FSInputFile(file_path)
            await bot.send_video(chat_id=message.chat.id, video=video_file, caption="✅ Bot orqali yuklab olindi")
            await status_msg.delete()
            os.remove(file_path)
        else:
            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi.")
    except Exception as e:
        logging.error(f"Error downloading instagram: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi. Link to'g'riligini yoki kontent ochiqligini tekshiring.")

# Musiqa qidirish (Qo'shiq nomi yozilganda)
@dp.message()
async def search_music(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("🔍 Qo'shiqlar qidirilmoqda...")

    ydl_opts = {
        'default_search': 'ytsearch5',
        'quiet': True,
        'extract_flat': True,
    }

    try:
        loop = asyncio.get_event_loop()
        def search():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch5:{query}", download=False)

        results = await loop.run_in_executor(None, search)
        entries = results.get('entries', [])

        if not entries:
            await status_msg.edit_text("❌ Hech qanday qo'shiq topilmadi.")
            return

        keyboard_buttons = []
        text = "🎶 **Topilgan qo'shiqlar:**\n\n"

        for idx, item in enumerate(entries, start=1):
            title = item.get('title', 'Noma\'lum qo\'shiq')
            video_id = item.get('id')
            text += f"{idx}. {title}\n"
            keyboard_buttons.append([InlineKeyboardButton(text=f"⬇️ {idx}. Yuklash", callback_data=f"dl_{video_id[:20]}")])

        kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await status_msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Search error: {e}")
        await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")

# Tugma bosilganda qo'shiqni MP3 qilib yuklab berish
@dp.callback_query(F.data.startswith("dl_"))
async def process_music_download(callback: CallbackQuery):
    video_id = callback.data.replace("dl_", "")
    await callback.answer("📥 Audio tayyorlanmoqda...")
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_filename = f"audio_{video_id}.mp3"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_filename,
        'quiet': True,
    }

    try:
        loop = asyncio.get_event_loop()
        def download_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await loop.run_in_executor(None, download_audio)

        if os.path.exists(out_filename):
            audio_file = types.FSInputFile(out_filename)
            await bot.send_audio(chat_id=callback.message.chat.id, audio=audio_file)
            os.remove(out_filename)
        else:
            await callback.message.answer("❌ Audioni yuklab bo'lmadi.")

    except Exception as e:
        logging.error(f"Audio download error: {e}")
        await callback.message.answer("❌ Yuklab olishda xatolik yuz berdi.")

# Web Server (Render 24/7 ishlashi uchun)
app = Flask('')

@app.route('/')
def home():
    return "Music & Instagram Bot Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def main():
    t = Thread(target=run_flask)
    t.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
  
