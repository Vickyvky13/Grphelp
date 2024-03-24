import datetime  
import os  
from asyncio import get_running_loop  
from functools import partial  
from io import BytesIO  
  
from pyrogram import filters  
from pytube import YouTube  
from requests import get  
  
from wbb import aiohttpsession as session  
from wbb import app, arq  
from wbb.core.decorators.errors import capture_err  
from wbb.utils.pastebin import paste  
  
__MODULE__ = "Music"  
__HELP__ = """  
/ytmusic [link] To Download Music From Various Websites Including Youtube. [SUDOERS]  
/saavn [query] To Download Music From Saavn.  
/lyrics [query] To Get Lyrics Of A Song.  
"""  
  
is_downloading = False  
  
  
def download_youtube_media(arq_resp):
    r = arq_resp.result[0]

    title = r.title
    performer = r.channel

    m, s = r.duration.split(":")
    duration = int(datetime.timedelta(minutes=int(m), seconds=int(s)).total_seconds())

    if duration > 1800:
        return

    thumb = get(r.thumbnails[0]).content
    with open("thumbnail.png", "wb") as f:
        f.write(thumb)
    thumbnail_file = "thumbnail.png"

    url = f"https://youtube.com{r.url_suffix}"
    yt = YouTube(url)
    
    # Downloading video
    video_stream = yt.streams.filter(file_extension='mp4', progressive=True).first()
    video_file = video_stream.download()

    # Downloading audio
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_file = audio_stream.download()

    return [title, performer, duration, audio_file, video_file, thumbnail_file]
  
  
@app.on_message(filters.command(["ytmusic", "song"]))  
@capture_err  
async def music(_, message):  
    global is_downloading  
    if len(message.command) < 2:  
        return await message.reply_text("/ytmusic needs a query as argument")  
  
    url = message.text.split(None, 1)[1]  
    if is_downloading:  
        return await message.reply_text(  
            "Another download is in progress, try again after sometime."  
        )  
    is_downloading = False 
  
    # Get the name of the user who requested the music 
    user_name = message.from_user.first_name if message.from_user else "Unknown User" 
  
    # Send a message indicating the start of the download process with the user's name 
    m = await message.reply_text(  
        f"{user_name.capitalize()} is downloading {url}", disable_web_page_preview=True  
    )  
    try:  
        loop = get_running_loop()  
        arq_resp = await arq.youtube(url)  
        music = await loop.run_in_executor(  
            None, partial(download_youtube_media, arq_resp)  
        )  
  
        if not music:  
            return await message.reply_text("[ERROR]: MUSIC TOO LONG")  
        (  
            title,  
            performer,  
            duration,  
            audio_file,  
            video_file,  
            thumbnail_file,  
        ) = music  
    except Exception as e:  
        is_downloading = False  
        return await m.edit(str(e))  
  
    # Mention the user who requested the music and send the audio file 
    await message.reply_video(  
        video_file,  
        duration=duration,  
        caption=f"{user_name.capitalize()}, here is your requested music video."  
    )  
  
    await message.reply_audio(  
        audio_file,  
        duration=duration,  
        performer=performer,  
        title=title,  
        thumb=thumbnail_file,  
        caption=f"{user_name.capitalize()}, here is your requested music audio."  # Mention the user with capitalized name 
    )  
  
    # Delete the command message 
    await message.delete()  
  
    await m.delete()  
    os.remove(audio_file)  
    os.remove(video_file)  
    os.remove(thumbnail_file)  
    is_downloading = False  
  
  
# Funtion To Download Song  
async def download_song(url):  
    async with session.get(url) as resp:  
        song = await resp.read()  
    song = BytesIO(song)  
    song.name = "a.mp3"  
    return song 
  
  
  
  
  
  
# Jiosaavn Music 
  
  
@app.on_message(filters.command("saavn")) 
@capture_err 
async def jssong(_, message): 
    global is_downloading 
    if len(message.command) < 2: 
        return await message.reply_text("/saavn requires an argument.") 
    if is_downloading: 
        return await message.reply_text( 
            "Another download
