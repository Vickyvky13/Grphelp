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
  
def download_youtube_media(arq_resp, download_audio=True):  
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

    if download_audio:  
        media_stream = yt.streams.filter(only_audio=True).get_audio_only()  
        out_file = media_stream.download()  
        base, _ = os.path.splitext(out_file)  
        media_file = base + ".mp3"  
    else:  
        media_stream = yt.streams.filter(progressive=True).first()  
        out_file = media_stream.download()  
        base, _ = os.path.splitext(out_file)  
        media_file = base + ".mp4"  

    os.rename(out_file, media_file)  

    return [title, performer, duration, media_file, thumbnail_file]  

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

    # Check if the user wants to download audio or video
    download_audio = True
    if len(message.command) > 2 and message.command[2] == "video":
        download_audio = False

    # Get the name of the user who requested the music 
    user_name = message.from_user.first_name if message.from_user else "Unknown User" 

    # Send a message indicating the start of the download process with the user's name 
    m = await message.reply_text(  
        f"{user_name.capitalize()} is downloading {url}", disable_web_page_preview=True  
    )  
    try:  
        loop = get_running_loop()  
        arq_resp = await arq.youtube(url)  
        media = await loop.run_in_executor(  
            None, partial(download_youtube_media, arq_resp, download_audio)  
        )  

        if not media:  
            return await message.reply_text("[ERROR]: MEDIA TOO LONG")  
        (  
            title,  
            performer,  
            duration,  
            media_file,  
            thumbnail_file,  
        ) = media  
    except Exception as e:  
        is_downloading = False  
        return await m.edit(str(e))  

    # Mention the user who requested the music and send the media file 
    if download_audio:  
        await message.reply_audio(  
            media_file,  
            duration=duration,  
            performer=performer,  
            title=title,  
            thumb=thumbnail_file,  
            caption=f"{user_name.capitalize()}, here is your requested music."  # Mention the user with capitalized name 
        )  
    else:  
        await message.reply_video(  
            media_file,  
            duration=duration,  
            performer=performer,  
            title=title,  
            thumb=thumbnail_file,  
            caption=f"{user_name.capitalize()}, here is your requested video."  # Mention the user with capitalized name 
        )  

    # Delete the command message 
    await message.delete()  

    await m.delete()  
    os.remove(media_file)  
    os.remove(thumbnail_file)  
    is_downloading = False  

# Function To Download Song  
async def download_song(url):  
    async with session.get(url) as resp:  
        media = await resp.read()  
    media = BytesIO(media)  
    media.name = "a.mp3"  
    return media  
  
# Jiosaavn Music   
@app.on_message(filters.command("saavn"))  
@capture_err  
async def jssong(_, message):  
    # Your existing code for Saavn music download with error handling  

# Lyrics   
@app.on_message(filters.command("lyrics"))  
async def lyrics_func(_, message):  
    # Your existing code for fetching lyrics with error handling
