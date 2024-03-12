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
    sender_mention = message.reply_to_message.from_user.mention
    sender_first_name = message.reply_to_message.from_user.first_name
    # Check if the command includes a mention
    if len(message.command) > 1:
        # Extract the mentioned user's name and append it to the text
        mentioned_user = message.command[1]
        text += f" {mentioned_user}"
    try:
        loop = get_running_loop()
        audio = await loop.run_in_executor(None, convert, text)
        caption = (
            f"Original message by {sender_first_name} ({sender_mention}): [Link to Message]({message.link})\n\n"
            f"Original message: {message.reply_to_message.text}"
        )
        await message.reply_audio(audio, caption=caption)
        await m.delete()
        audio.close()
    except Exception as e:
        await m.edit(str(e))
        e = traceback.format_exc()
        print(e)
