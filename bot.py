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
        
        if file_path and os.path.exists(file_path):
            video_file = types.FSInputFile(file_path)
            await bot.send_video(chat_id=message.chat.id, video=video_file, caption="✅ Bot orqali yuklab olindi")
            await status_msg.delete()
            os.remove(file_path)
        else:
            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi.")
    except Exception as e:
        logging.error(f"Error downloading instagram: {e}")
        await status_msg.edit_text("❌ Videoni yuklab olishda xatolik yuz berdi. Boshqa linkni sinab ko'ring.")

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
            row.append(InlineKeyboardButton(text=str(idx), callback_data=f"s_{video_id}"))
            
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

@dp.callback_query(F.data.startswith("s_"))
async def process_music_download(callback: CallbackQuery):
    video_id = callback.data.replace("s_", "")
    await callback.answer("📥 Audio tayyorlanmoqda, iltimos kuting...")
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Xatolik chiqarmasligi uchun eng universal yuklash sozlamalari
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl:': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    # Agar ffmpeg bo'lmasa oddiy usulda yuklab beruvchi zaxira sozlama
    fallback_opts = {
        'format': 'best',
        'quiet': True,
    }

    file_path = None
    try:
        loop = asyncio.get_event_loop()
        
        def download_audio():
            # Oldingi qolgan fayllarni tozalash
            for f in os.listdir('.'):
                if f.startswith('audio_'):
                    try:
                        os.remove(f)
                    except:
                        pass
                        
            local_opts = {
                'format': 'bestaudio',
                'outtmpl': f'audio_{video_id}.%(ext)s',
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(local_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await loop.run_in_executor(None, download_audio)

        if file_path and os.path.exists(file_path):
            audio_file = types.FSInputFile(file_path)
            await bot.send_audio(chat_id=callback.message.chat.id, audio=audio_file, caption="🎵 @my_music_saver_2026_bot")
            try:
                os.remove(file_path)
            except:
                pass
        else:
            await callback.message.answer("⚠️ Kechirasiz, bu qo'shiqni yuklab bo'lmadi. Boshqa raqamni tanlab ko'ring.")

    except Exception as e:
        logging.error(f"Audio download error: {e}")
        # Agar asosiy usul ishlamasa, zaxira oddiy formatda yuborishga urinib ko'ramiz
        try:
            def download_fallback():
                fallback_filename = f'audio_fallback_{video_id}.mp4'
                f_opts = {'format': 'best', 'outtmpl': fallback_filename, 'quiet': True}
                with yt_dlp.YoutubeDL(f_opts) as ydl:
                    ydl.download([url])
                return fallback_filename

            fallback_path = await loop.run_in_executor(None, download_fallback)
            if fallback_path and os.path.exists(fallback_path):
                audio_file = types.FSInputFile(fallback_path)
                await bot.send_audio(chat_id=callback.message.chat.id, audio=audio_file, caption="🎵 @my_music_saver_2026_bot")
                os.remove(fallback_path)
            else:
                await callback.message.answer("❌ Bu qo'shiqni yuklab bo'lmadi, boshqa qo'shiqni tanlang.")
        except Exception as err:
            logging.error(f"Fallback error: {err}")
            await callback.message.answer("❌ Yuklab olish imkoni bo'lmadi. Boshqa qo'shiqni tanlab ko'ring.")

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
        
