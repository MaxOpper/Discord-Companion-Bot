import discord
from discord.ext import commands
import yt_dlp
import g4f
from gtts import gTTS
from SetUp import TOKEN, IDENTITY
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Add this line
intents.voice_states = True  # Enable voice state tracking
bot = commands.Bot(command_prefix='!', intents=intents)
voice_client = None



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

@bot.command(name='play', help='Play audio from a YouTube link or search query')
async def youtube(ctx, *, query: str = None):
    if not query:
        await ctx.send("Please provide a YouTube link or search query.")
        return
    
    bot_channel = discord.utils.get(ctx.guild.text_channels, name='bot')

    voice_channel = discord.utils.get(bot.guilds[0].voice_channels, name="General")

    global voice_client
    if not voice_client or not voice_client.is_connected():
        voice_client = await voice_channel.connect()

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/song.%(ext)s',
    }

    # Check if the query is a URL or just a search string
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

    voice_client.play(discord.FFmpegPCMAudio('downloads/song.mp3', options='-filter:a "volume=0.15"'))
    await bot_channel.send(f"Playing: {info_dict['title']}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please provide a YouTube link.')

@bot.command(name='skip', help='Stop the currently playing song or TTS')
async def skip(ctx):
    global voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Skipped the current playback!")
    else:
        await ctx.send("No audio is currently playing.")

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

async def tts(text, voice_client):
    
    tts = gTTS(text=text, lang='en-uk')
    print(text)
    tts.save('tts.mp3')
    voice_client.play(discord.FFmpegPCMAudio('tts.mp3', options='-filter:a "volume=0.15"'))
bot.run(TOKEN)
