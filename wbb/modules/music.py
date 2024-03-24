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
/vsong [link] To Download Video From YouTube. [SUDOERS]  
"""  

is_downloading = False  


def download_youtube_audio(arq_resp):  
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
    audio = yt.streams.filter(only_audio=True).get_audio_only()  

    out_file = audio.download()  
    base, _ = os.path.splitext(out_file)  
    audio_file = base + ".mp3"  
    os.rename(out_file, audio_file)  

    return [title, performer, duration, audio_file, thumbnail_file]  


def download_youtube_video(url):
    yt = YouTube(url)
    video = yt.streams.get_highest_resolution()
    out_file = video.download()
    return out_file


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

    user_name = message.from_user.first_name if message.from_user else "Unknown User" 

    m = await message.reply_text(  
        f"{user_name.capitalize()} is downloading {url}", disable_web_page_preview=True  
    )  
    try:  
        loop = get_running_loop()  
        arq_resp = await arq.youtube(url)  
        music = await loop.run_in_executor(  
            None, partial(download_youtube_audio, arq_resp)  
        )  

        if not music:  
            return await message.reply_text("[ERROR]: MUSIC TOO LONG")  
        (  
            title,  
            performer,  
            duration,  
            audio_file,  
            thumbnail_file,  
        ) = music  
    except Exception as e:  
        is_downloading = False  
        return await m.edit(str(e))  

    await message.reply_audio(  
        audio_file,  
        duration=duration,  
        performer=performer,  
        title=title,  
        thumb=thumbnail_file,  
        caption=f"{user_name.capitalize()}, here is your requested music."  
    )  

    await message.delete()  
    await m.delete()  
    os.remove(audio_file)  
    os.remove(thumbnail_file)  
    is_downloading = False  


@app.on_message(filters.command(["vsong", "video"]))  
@capture_err  
async def video(_, message):  
    global is_downloading  
    if len(message.command) < 2:  
        return await message.reply_text("/vsong needs a YouTube link as argument")  

    url = message.text.split(None, 1)[1]  
    if is_downloading:  
        return await message.reply_text(  
            "Another download is in progress, try again after sometime."  
        )  
    is_downloading = False 

    user_name = message.from_user.first_name if message.from_user else "Unknown User" 

    m = await message.reply_text(  
        f"{user_name.capitalize()} is downloading {url}", disable_web_page_preview=True  
    )  
    try:  
        video_file = await download_youtube_video(url)
    except Exception as e:  
        is_downloading = False  
        return await m.edit(str(e))  

    await message.reply_video(  
        video_file,  
        caption=f"{user_name.capitalize()}, here is your requested video."  
    )  

    await message.delete()  
    await m.delete()  
    os.remove(video_file)  
    is_downloading = False  

# The rest of the code remains unchanged...
