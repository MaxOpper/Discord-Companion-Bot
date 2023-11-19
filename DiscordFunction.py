import discord
from discord.ext import commands
import yt_dlp
import g4f
from gtts import gTTS
import asyncio
import time
import os, glob

from SetUp import TOKEN, IDENTITY
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Add this line
intents.voice_states = True  # Enable voice state tracking
bot = commands.Bot(command_prefix='!', intents=intents)
voice_client = None
song_queue = []
is_downloading = False

# Define a global voice_client variable initially set to None
voice_client = None

@bot.event
async def on_ready():
    global voice_client  # Declare the variable as global
    
    print(f'{bot.user.name} has connected to Discord!')
    voice_channel = discord.utils.get(bot.guilds[0].voice_channels, name="General")

    if voice_channel:
        if voice_client is None:  # Check if it's the first time connecting
            voice_client = await voice_channel.connect()
        
        else:
            await voice_client.move_to(voice_channel)  # Move to the specified channel
    else:
        print("Voice channel not found.")


@bot.event
async def on_message(message):
    if message.author.bot:
        if '!replay' in message.content.lower():
            await play(message.channel)
        if '!skip' in message.content.lower():
            await skip(message.channel)
        if '!play' in message.content.lower():
            # Split the message by '!play' and strip leading and trailing whitespaces
            content_after_play = message.content.split('!play', 1)[1].strip()
            # Call the youtube function with the content after '!play'
            ctx = discord.utils.get(bot.guilds[0].voice_channels, name="General")
            await youtube(ctx, query = content_after_play)
        if ':pear:' in message.content:
            await tts(message.content, voice_client)

    await bot.process_commands(message)

@bot.command(name='replay', help='Play an MP3 file')
async def play(ctx):
    # Check if the user is in a voice channel
    if voice_client:
        voice_client.play(discord.FFmpegPCMAudio('downloads\song.mp3', options='-filter:a "volume=0.15"'))  # Replace 'your_audio.mp3' with the path to your MP3 file
        await ctx.send("Running that last one back")
    else:
        await ctx.send("You need to be in a voice channel to use this command.")

async def play_next(ctx):
    global voice_client
    if song_queue:
        next_song = song_queue.pop(0)
        ctx = discord.utils.get(bot.guilds[0].voice_channels, name="General")
        await youtube(ctx, query = next_song)

def play_next_wrapper(error):
    ctx = discord.utils.get(bot.guilds[0].voice_channels, name="General")

    if error:
        print(f"Playback error: {error}")
    
    fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
    try:
        fut.result()
    except Exception as e:
        print(f"Error in play_next: {e}")

    # Check if the queue is empty and voice client is not playing
    if not song_queue and (not voice_client or not voice_client.is_playing()):
        cleanup_downloads_folder()


def cleanup_downloads_folder():
    # Path to the downloads folder
    downloads_folder = 'downloads/'

    # Find all .mp3 files in the folder
    mp3_files = glob.glob(os.path.join(downloads_folder, '*.mp3'))

    # Delete each file
    for file_path in mp3_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

@bot.command(name='play', help='Play audio from a YouTube link or search query')
async def youtube(ctx, *, query: str = None):
    global is_downloading
    if not query:
        await ctx.send("Please provide a YouTube link or search query.")
        return
    
    bot_channel = discord.utils.get(ctx.guild.text_channels, name='bot')

    voice_channel = discord.utils.get(bot.guilds[0].voice_channels, name="General")

    global voice_client
    if not voice_client or not voice_client.is_connected():
        voice_client = await voice_channel.connect()
    unique_filename = f'downloads/song_{int(time.time())}'
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': unique_filename,
    }

    if voice_client.is_playing() or voice_client.is_paused() or is_downloading == True:
        song_queue.append(query)
        await ctx.send("```yaml\n" + f"Added to queue: {query}" + "```")
    else:
        is_downloading = True
        if "http" in query or "www" in query:
            url = query
        else:
            query = query + " lyrics"
            # Perform a search to find the first video matching the query
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_result = ydl.extract_info(f"ytsearch:{query}", download=False)
                url = search_result['entries'][0]['webpage_url']

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_length = info_dict.get('duration')

            if video_length > 420:
                await bot_channel.send("The song is too long!")
                return

            ydl.download([url])
        is_downloading = False
        voice_client.play(discord.FFmpegPCMAudio(unique_filename + ".mp3", options='-filter:a "volume=0.15"'), after=play_next_wrapper)
        await bot_channel.send("```yaml\n" + f"Playing: {info_dict['title']}" + "```")
        


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please provide a YouTube link.')

@bot.command(name='skip', help='Stop the currently playing song or TTS')
async def skip(ctx):
    global voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await ctx.send("```yaml\n" + "Skipped the current playback!" + "```")
        await play_next(ctx)  # Call play_next to immediately start the next song
    else:
        await ctx.send("```yaml\n" + "No audio is currently playing." + "```")


@bot.command(name='ringo', help='Prompt our AI companion')
async def ringo(ctx, *, query: str = None):
    content = IDENTITY + query
    print(content)
    res = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": content}],
            proxy="http://host:port",
            # or socks5://user:pass@host:port
            timeout=120,  # in secs
        )
    res = res + " :pear:"
    await ctx.send(f"{res}")

@bot.command(name='queue', help='Displays the current song queue')
async def queue(ctx):
    if not song_queue:
        await ctx.send("```yaml\n" + "The queue is currently empty." + "```")
        return

    # Constructing the queue message with capitalized song titles
    queue_message = "Current Queue:\n"
    for index, song in enumerate(song_queue, start=1):
        capitalized_song = song.title()  # Capitalize the first letter of each word
        queue_message += f"{index}. {capitalized_song}\n"

    await ctx.send("```yaml\n" + queue_message + "```")


@bot.command(name='clear', help='Clears the song queue')
async def queue(ctx):
    if not song_queue:
        await ctx.send("```yaml\n Queue is already empty!```")
    else:
        song_queue.clear()
        await ctx.send("```yaml\n Queue cleared!```")

async def tts(text, voice_client):
    
    tts = gTTS(text=text, lang='en-uk')
    print(text)
    tts.save('tts.mp3')
    voice_client.play(discord.FFmpegPCMAudio('tts.mp3', options='-filter:a "volume=0.15"'))
bot.run(TOKEN)
