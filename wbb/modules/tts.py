import traceback
from asyncio import get_running_loop
from io import BytesIO

from googletrans import Translator
from gtts import gTTS
from pyrogram import filters
from pyrogram.types import Message

from wbb import app


def convert(text):
    audio = BytesIO()
    i = Translator().translate(text, dest="en")
    lang = i.src
    tts = gTTS(text, lang=lang)
    audio.name = lang + ".mp3"
    tts.write_to_fp(audio)
    return audio


@app.on_message(filters.command("tts"))
async def text_to_speech(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to some text ffs.")
    if not message.reply_to_message.text:
        return await message.reply_text("Reply to some text ffs.")
    m = await message.reply_text("Processing")
    text = message.reply_to_message.text
    sender_id = message.from_user.id
    sender_mention = f"[User](tg://user?id={sender_id})"
    try:
        loop = get_running_loop()
        audio = await loop.run_in_executor(None, convert, text)
        caption = f"Text to Speech\n\nRequested by {sender_mention}"
        await message.reply_audio(audio, caption=caption, parse_mode="markdown")
        await m.delete()
        audio.close()
    except Exception as e:
        await m.edit(str(e))
        e = traceback.format_exc()
        print(e)
