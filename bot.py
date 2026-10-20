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

user_data = {}

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        "👋 **Xush kelibsiz!**\n\n"
        "1. **Instagram** havolasini yuborib videoni yuklab olishingiz mumkin.\n"
        "2. **Qo'shiq nomi**ni yozib musiqalarni qidirishingiz mumkin."
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(F.text.contains("instagram.com"))
async def download_instagram(message: types.Message):
    status_msg = await message.answer("📥 Instagram video yuklanmoqda...")
    url = message.text.strip()

    file_id = f"insta_{message.from_user.id}_{message.message_id}"
    ydl_opts = {
        'format': 'mp4/best',
        'outtmpl': f'{file_id}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        
        file_path = await loop.run_in_executor(None, download)
        
        if file_path and os.path.exists(file_path):
            video_file = types.FSInputFile(file_path)
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎧 Videodagi qo'shiqni yuklash", callback_data=f"insta_audio_{file_id}")]
            ])
            await bot.send_video(
                chat_id=message.chat.id, 
                video=video_file, 
                caption="✅ Bot orqali yuklab olindi\n\n@my_music_saver_2026_bot",
                reply_markup=kb
            )
            await status_msg.delete()
            user_data[file_id] = file_path
        else:
            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi.")
    except Exception as e:
        logging.error(f"Error downloading instagram: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi.")

@dp.callback_query(F.data.startswith("insta_audio_"))
async def process_insta_audio(callback: CallbackQuery):
    file_id = callback.data.replace("insta_audio_", "")
    file_path = user_data.get(file_id)
    
    if file_path and os.path.exists(file_path):
        await callback.answer("🎧 Audio yuborilmoqda...")
        audio_file = types.FSInputFile(file_path, filename="instagram_audio.mp3")
        await bot.send_audio(
            chat_id=callback.message.chat.id, 
            audio=audio_file, 
            caption="🎵 Videodan ajratib olingan audio\n\n@my_music_saver_2026_bot"
        )
    else:
        await callback.answer("❌ Audio fayl topilmadi.", show_alert=True)

@dp.message()
async def search_music(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer("🔍 Qo'shiqlar qidirilmoqda...")

    ydl_opts = {
        'default_search': 'ytsearch10',
        'quiet': True,
        'extract_flat': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        loop = asyncio.get_event_loop()
        def search():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch10:{query}", download=False)

        results = await loop.run_in_executor(None, search)
        entries = results.get('entries', [])

        if not entries:
            await status_msg.edit_text("❌ Hech qanday qo'shiq topilmadi.")
            return

        text = "🎶 **Topilgan qo'shiqlar:**\n\n"
        keyboard_buttons = []
        row = []

        for idx, item in enumerate(entries, start=1):
            title = item.get('title', 'Noma\'lum qo\'shiq')
            text += f"{idx}. {title}\n"
            video_id = item.get('id')
            if video_id:
                row.append(InlineKeyboardButton(text=str(idx), callback_data=f"dl_{video_id}"))
                if len(row) == 5:
                    keyboard_buttons.append(row)
                    row = []

        if row:
            keyboard_buttons.append(row)

        kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await status_msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Search error: {e}")
        await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")

@dp.callback_query(F.data.startswith("dl_"))
async def process_music_download(callback: CallbackQuery):
    video_id = callback.data.replace("dl_", "")
    await callback.answer("📥 Audio yuklab olinmoqda, kuting...")
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_filename = f"music_{video_id}.m4a"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_filename,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        loop = asyncio.get_event_loop()
        def download_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return out_filename

        file_path = await loop.run_in_executor(None, download_audio)

        if file_path and os.path.exists(file_path):
            audio_file = types.FSInputFile(file_path, filename=f"audio_{video_id}.mp3")
            await bot.send_audio(
                chat_id=callback.message.chat.id, 
                audio=audio_file, 
                caption="🎵 @my_music_saver_2026_bot"
            )
            os.remove(file_path)
        else:
            await callback.message.answer("❌ Bu qo'shiqni yuklab bo'lmadi. Boshqasini tanlab ko'ring.")

    except Exception as e:
        logging.error(f"Audio download error: {e}")
        await callback.message.answer("❌ Kechirasiz, bu qo'shiqni yuklab olish imkoni bo'lmadi. Boshqasini tanlab ko'ring.")

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
    
