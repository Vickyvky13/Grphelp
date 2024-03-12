import traceback 
from asyncio import get_running_loop 
from io import BytesIO 

from googletrans import Translator 
from gtts import gTTS 
from pyrogram import filters 
from pyrogram.types import Message 

from wbb import app 


def convert(text, speed=1.0): 
    audio = BytesIO() 
    i = Translator().translate(text, dest="en") 
    lang = i.src 
    tts = gTTS(text, lang=lang, speed=speed) 
    audio.name = lang + ".mp3" 
    tts.write_to_fp(audio) 
    return audio 


@app.on_message(filters.command("tts")) 
async def text_to_speech(_, message: Message): 
    if not message.reply_to_message: 
        return await message.reply_text("Reply to some text ffs.") 
    if not message.reply_to_message.text: 
        return await message.reply_text("Reply to some text ffs.") 
    args = message.text.split()[1:]
    speed = 1.0
    if args and args[0].replace('.', '', 1).isdigit():
        speed = float(args[0])
    m = await message.reply_text("Processing") 
    text = message.reply_to_message.text 
    sender_mention = message.reply_to_message.from_user.mention 
    try: 
        loop = get_running_loop() 
        audio = await loop.run_in_executor(None, convert, text, speed) 
        caption = f"Original message by {sender_mention}: [Link to Message]({message.link})"
        await message.reply_audio(audio, caption=caption) 
        await m.delete() 
        audio.close() 
    except Exception as e: 
        await m.edit(str(e)) 
        e = traceback.format_exc() 
        print(e)
