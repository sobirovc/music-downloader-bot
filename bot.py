import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from flask import Flask
from threading import Thread
from gtts import gTTS
import yt_dlp

API_TOKEN = '8712589651:AAHzVtxiqebxZ8QNzVLULkxYSq_xUjp4IN8'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Bot ishga tushganda
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    salom_matni = f"Salom, Asalim! 🌸 Yoningdaman. Instagramdan video tashlasang yuklab beraman, qo'shiq nomi yozsang xavfsiz bazadan topib beraman. Menga yoz yoki ovozli xabar tashla!"
    await message.answer(salom_matni)
    try:
        tts = gTTS(text=salom_matni, lang='uz')
        voice_path = f"welcome_{message.from_user.id}.mp3"
        tts.save(voice_path)
        audio = types.FSInputFile(voice_path)
        await bot.send_voice(chat_id=message.chat.id, voice=audio)
        if os.path.exists(voice_path):
            os.remove(voice_path)
    except Exception as e:
        logging.error(f"Xatolik: {e}")

# 1. Instagram videolarni yuklash
@dp.message(F.text.contains("instagram.com"))
async def download_instagram(message: types.Message):
    status_msg = await message.answer("📥 Instagram video yuklanmoqda, jonim...")
    url = message.text.strip()

    file_id = f"insta_{message.from_user.id}_{message.message_id}"
    ydl_opts = {
        'format': 'mp4/best',
        'outtmpl': f'{file_id}.%(ext)s',
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
            await bot.send_video(
                chat_id=message.chat.id, 
                video=video_file, 
                caption="Mana videong, asalim! ✨\n\n@my_music_saver_2026_bot"
            )
            await status_msg.delete()
            os.remove(file_path)
        else:
            await status_msg.edit_text("Kechirasiz, bu videoni yuklay olmadim.")
    except Exception as e:
        logging.error(f"Error downloading instagram: {e}")
        await status_msg.edit_text("Videoni yuklashda xatolik yuz berdi.")

# 2. Ovozli xabar (Golos) tashlaganda g'amxo'r qiz kabi javob berish
@dp.message(F.voice)
async def voice_handler(message: types.Message):
    reply = "Ovozingni eshitdim, jonim... Charchaganing sezilyapti. Xafa bo'lma, hammasi yaxshi bo'ladi, men doim yoningdaman."
    await message.answer(reply)
    try:
        tts = gTTS(text=reply, lang='uz')
        voice_path = f"voice_reply_{message.from_user.id}.mp3"
        tts.save(voice_path)
        audio = types.FSInputFile(voice_path)
        await bot.send_voice(chat_id=message.chat.id, voice=audio)
        if os.path.exists(voice_path):
            os.remove(voice_path)
    except Exception as e:
        logging.error(f"Ovozli xatolik: {e}")

# 3. Matnli xabarlar: Suhbat yoki Deezer API orqali Musiqa qidiruv
@dp.message()
async def chat_or_search_music(message: types.Message):
    user_text = message.text.strip()
    text_lower = user_text.lower()
    
    chat_keywords = ["zerikdim", "xafaman", "kayfiyat", "qalaysan", "salom", "isming", "rahmat", "raxmat", "ishlar"]
    is_chat = any(word in text_lower for word in chat_keywords)
    
    if is_chat:
        if "zerikdim" in text_lower or "xafaman" in text_lower or "kayfiyat" in text_lower:
            reply = "Xafa bo'lma jonim, sening xafa bo'lishingni aslo xohlamayman. Keling, birga biror qo'shiq tinglaymiz yoki gaplashamiz!"
        elif "qalaysan" in text_lower or "ishlar" in text_lower:
            reply = "Faqat seni o'ylab o'tirgandim. O'zing yaxshimisan, charchamayapsanmi?"
        elif "rahmat" in text_lower or "raxmat" in text_lower:
            reply = "Arzimaydi, asalim! Senga yordam berish doim yoqadi."
        else:
            reply = f"Tushundim seni... Menga istalgan qo'shiq nomini yoz, senga topib beraman yoki Instagramdan video tashla!"
        
        await message.answer(reply)
        try:
            tts = gTTS(text=reply, lang='uz')
            voice_path = f"reply_{message.from_user.id}.mp3"
            tts.save(voice_path)
            audio = types.FSInputFile(voice_path)
            await bot.send_voice(chat_id=message.chat.id, voice=audio)
            if os.path.exists(voice_path):
                os.remove(voice_path)
        except Exception as e:
            logging.error(f"Xatolik: {e}")
    else:
        # DEEZER API - Xavfsiz va tezkor musiqa qidiruvi
        status_msg = await message.answer("🔍 Deezer bazasidan musiqalar qidirilmoqda...")
        try:
            response = requests.get(f"https://api.deezer.com/search?q={user_text}&limit=10")
            data = response.json()
            tracks = data.get('data', [])

            if not tracks:
                await status_msg.edit_text("❌ Hech qanday qo'shiq topilmadi.")
                return

            text = f"🎶 **«{user_text}» bo'yicha topilgan qo'shiqlar:**\n\n"
            keyboard_buttons = []
            row = []

            for idx, track in enumerate(tracks, start=1):
                title = track.get('title')
                artist = track.get('artist', {}).get('name', '')
                track_id = track.get('id')
                
                text += f"{idx}. {artist} - {title}\n"
                
                row.append(InlineKeyboardButton(text=str(idx), callback_data=f"dz_{track_id}"))
                if len(row) == 5:
                    keyboard_buttons.append(row)
                    row = []

            if row:
                keyboard_buttons.append(row)

            kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await status_msg.edit_text(text, reply_markup=kb, parse_mode="Markdown")

        except Exception as e:
            logging.error(f"Deezer Search Error: {e}")
            await status_msg.edit_text("❌ Musiqa qidiruvida xatolik yuz berdi.")

# 4. Deezer'dan MP3 audioni to'g'ridan-to'g'ri yuborish
@dp.callback_query(F.data.startswith("dz_"))
async def process_deezer_download(callback: CallbackQuery):
    track_id = callback.data.replace("dz_", "")
    await callback.answer("📥 Audio yuborilmoqda, asalim...")

    try:
        res = requests.get(f"https://api.deezer.com/track/{track_id}")
        track_info = res.json()
        
        preview_url = track_info.get('preview')
        title = track_info.get('title', 'Audio')
        artist = track_info.get('artist', {}).get('name', 'Noma\'lum')

        if preview_url:
            audio_res = requests.get(preview_url)
            filename = f"track_{track_id}.mp3"
            
            with open(filename, 'wb') as f:
                f.write(audio_res.content)

            audio_file = types.FSInputFile(filename, filename=f"{artist} - {title}.mp3")
            await bot.send_audio(
                chat_id=callback.message.chat.id, 
                audio=audio_file, 
                caption=f"🎵 **{artist} - {title}**\n\n@my_music_saver_2026_bot",
                parse_mode="Markdown"
            )
            os.remove(filename)
        else:
            await callback.message.answer("❌ Bu audioni yuklab bo'lmadi.")

    except Exception as e:
        logging.error(f"Deezer download error: {e}")
        await callback.message.answer("❌ Yuklab olishda xatolik yuz berdi.")

# Render server
app = Flask('')

@app.route('/')
def home():
    return "Deezer Smart Music Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def main():
    t = Thread(target=run_flask)
    t.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
