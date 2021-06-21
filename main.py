import asyncio
from asyncio.tasks import wait_for
from logging import setLogRecordFactory
import time
import discord
import os
from discord import message
from discord import channel
from discord import guild
from discord.colour import Colour 
from discord.ext import commands
from discord.member import Member, VoiceState
import youtube_dl
import pafy
import json

# Enter your Discord token here
DISCORD_TOKEN = ''

# Discord Configuration
intents = discord.Intents().all()
client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix='>', intents=intents)

print(intents.voice_states)

# # Youtube Configuration
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume = 0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        yt_audio(url)
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return yt_audio(url)




# Bot configuration

song_queue = []
config_file = open("config.json", 'r')
server_dict = json.load(config_file)

@client.event
async def on_message(message):
    time.sleep(2)
    if (message.author != client.user and (message.channel == discord.utils.get(message.guild.channels, name='hbm-songrequests'))):
        await message.delete()
        
    if message.content == ", setup":
        guild = message.guild
        print(discord.utils.get(guild.text_channels, name='hbm-songrequests'))
        if discord.utils.get(guild.text_channels, name='hbm-songrequests'):
            channel = discord.utils.get(guild.text_channels, name='hbm-songrequests')
            embed = discord.Embed(colour = Colour.orange(), title = 'Message', description='Already set up in ' + channel.mention)
            await message.channel.send(embed=embed)
        else:
            await guild.create_text_channel('hbm-songrequests')
            channel = discord.utils.get(guild.channels, name='hbm-songrequests')
            embed = discord.Embed(colour = Colour.green(), title = 'Success', description = 'Setup Complete! Play some awesome music in ' + channel.mention)
            await message.channel.send(embed = embed)
            for guild in client.guilds:
                for channel in guild.text_channels:
                    if channel.name == "hbm-songrequests":
                        message = discord.Embed(title='Nothing Playing Currently',colour=Colour.blue(), description = '').set_image(url='https://images.pexels.com/photos/1363876/pexels-photo-1363876.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260')
                        embed_message = await channel.send(embed=message)
                        append_id = open("config.json", 'w')
                        server_dict[guild.id] = embed_message.id
                        print("Server", server_dict)
                        json.dump(server_dict, append_id)
                        append_id.close()
    elif message.channel.name != 'hbm-songrequests':
        print("Ignored", message.channel.name)
        return
    elif message.content == 'join':
        await join(message)
    elif message.content == 'leave':
        await leave(message)
    elif message.content == 'pause':
        await pause(message)
    elif message.content == 'resume':
        await resume(message)
    elif message.content == 'stop':
        await stop(message)
    elif message.content == 'skip':
        await skip(message)
    elif message.content == 'clear':
        song_queue = []
        q = []
    elif message.author != client.user:
        await play(message)
    




@client.event
async def on_ready():
    print("Ready")
    # await channel.send(file=discord.File())0


# @client.event
# async def on_voice_state_update(client: Member, before: VoiceState, after: VoiceState):
#     print("Next Song")
#     if not after.channel:
#         return
#     guild = after.channel.guild
#     voice = guild.voice_client
#     if voice is None:
#         return
    
#     if song_queue == []:
#         return
#     elif voice.is_playing() == False and len(song_queue)>0:
#         print('next')
#         await play(song_queue[0])
#         song_queue.remove(song_queue[0])
#     else:
#       return

@bot.command(name='skip', help='Skip currently playing song')
async def skip(ctx):
    voice = ctx.guild.voice_client
    voice.stop()
    try:
        channel = discord.utils.get(ctx.guild.text_channels, name='hbm-songrequests')
        video = ytdl.extract_info(f"ytsearch:{song_queue[0].content}", download=False)['entries'][0]
        audio_url = pafy.new(video['webpage_url']).getbestaudio().url
        voice.play(discord.FFmpegPCMAudio(audio_url))
        del song_queue[0]
        
        embed = discord.Embed(title='**Now Playing: **', colour=Colour.blue(), description= video['title']).set_image(url=video['thumbnail'])
        # await ctx.channel.send(embed=embed)
        message = await ctx.channel.fetch_message(server_dict[str(ctx.guild.id)])
        await message.edit(embed = embed)
    except Exception as ex:
        print(ex)
        await ctx.channel.send("Something went wrong")  

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    print("Joined")
    if not ctx.author.voice:
        await ctx.channel.send("{} is not connected to a voice channel".format(ctx.author.name))
        return
    else:
        channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    print("Left")
    voice_client = ctx.guild.voice_client
    try:
        if voice_client.is_connected():
            await voice_client.disconnect()
    except Exception as ex:
        print(ex)
        await ctx.channel.send("The bot is not connnected to a voice channel.")

# @bot.command(name='play', help='To play a song')
# async def play(ctx, url):
#     print("Playing")
#     try:
#         server = ctx.guild
#         voice_channel = server.voice_client
#         if voice_channel.is_playing():
#             await ctx.channel.send("Already playing something else")
#             return
#         async with ctx.channel.typing():
#             # filename = await YTDLSource.from_url(str(url))
#             video = ytdl.extract_info(f"ytsearch:{url}", download=False)['entries'][0]
#             audio_url = pafy.new(video['webpage_url']).getbestaudio().url
#             voice_channel.play(discord.FFmpegPCMAudio(audio_url))
#             embed = discord.Embed(title='**Now Playing: **', colour=Colour.blue(), description=video['title'])
#             await ctx.channel.send(embed=embed)
#             # while voice_channel.is_playing:
                
#             # os.remove(filename)
#     except Exception as ex:
#         print(ex)
#         await ctx.channel.send("The bot is not connected to a voice channel")
#         return

@bot.command(name='play', help='To play a song')
async def play(ctx):
    server = ctx.guild
    voice_channel = server.voice_client

    song_queue.append(ctx)
    q = []
    for i in range(len(song_queue)):
        q.append(song_queue[i].content)
    print(q)
     
    if len(song_queue) > 1: 
        print("Waiting", ctx.guild.voice_client.is_playing())
        await client.wait_for(voice_channel, check= lambda ctx: voice_channel.is_playing() == False)
        print("Wait over")
    try:
        video = ytdl.extract_info(f"ytsearch:{song_queue[0].content}", download=False)['entries'][0]
        audio_url = pafy.new(video['webpage_url']).getbestaudio().url
        voice_channel.play(discord.FFmpegPCMAudio(audio_url))
        if len(song_queue)==0:
            embed =  discord.Embed(title='Nothing Playing Currently',colour=Colour.blue() ,description = '').set_image(url='https://images.pexels.com/photos/1363876/pexels-photo-1363876.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260')
        else:
            embed = discord.Embed(title='**Now Playing: **', colour=Colour.blue(), description= video['title']).set_image(url=video['thumbnail'])

        del song_queue[0]
        # await ctx.channel.send(embed=embed)
        # await client.wait_for('voice_clients', check=ctx.guild.voice_client.is_playing() == False)
        print(server_dict, 'Hello 1')
        print(server.id, "ID")
        print(server_dict[str(server.id)], 'Hello 2')
        message = await ctx.channel.fetch_message(server_dict[str(server.id)])
        print(message, 'Hello 3')
        await message.edit(embed = embed)
    except Exception as ex:
        print("Exception: ", ex)
        await ctx.channel.send("Something went wrong")
            

@bot.command(name='pause', help='To pause a song')
async def pause(ctx):
    print("Pausing")
    voice_client = ctx.guild.voice_client
    try:
        if voice_client.is_playing():
            voice_client.pause()
    except Exception as ex:
        print(ex)
        await ctx.channel.send("The bot is not playing anything at the moment")

@bot.command(name='resume', help='To resume a song')
async def resume(ctx):
    print("Resuming")
    voice_client = ctx.guild.voice_client
    try:
        if voice_client.is_paused():
            voice_client.resume()
    except Exception as ex:
        print(ex)
        await ctx.channel.send("The bot is not playing anything at the moment, play something by typing the name of the song in #hbm-songrequests")


@bot.command(name='stop', help='To stop currently playing song')
async def stop(ctx):
    print("Stopping")
    voice_client = ctx.guild.voice_client
    try:
        if voice_client.is_playing():
            voice_client.stop()
    except Exception as ex:
        print(ex)
        await ctx.channel.send("The bot is not playing anything at the moment")


# Running the bot
client.run(DISCORD_TOKEN)