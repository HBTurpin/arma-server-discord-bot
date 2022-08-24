from http import server
from pydoc import describe
from sqlite3 import Time
from sre_constants import MIN_UNTIL
from turtle import color
from discord.ext import commands
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import dotenv_values
import datetime
import requests
import os
import os.path
import re
import shutil
import sys
import json
import a2s

config = dotenv_values(".env")
TOKEN = "MjU3NTY4MDA4MjM3NDgxOTg1.GX5Pnm.EyLUXyHqAz-17L7Tq5lmTB4WKXu-2pbtMpRVKI"

from interactions.ext.get import get
import interactions

client = interactions.Client(TOKEN)






#JSON Handling
async def setup_message(id, channel_id, display_name, ip, port, server_name="", mods_required="", mods_clientside=""):
    with open("messages.json", "r+") as f:
        jd = json.load(f)
        jd[str(id)] = {
            "channel_id" : channel_id,
            "display_name" : display_name,
            "server_name" : server_name,
            "ip": ip,
            "port" : port
        }
        f.seek(0)
        json.dump(jd, f, indent=1)
    f.close()






#Status Upddating
async def update_status(id, channel_id, display_name, ip, port, server_name="", mods_required="", mods_clientside=""):
    try:
        message = await get(client, interactions.Message, channel_id=int(channel_id), message_id=int(id))
    except Exception:
        #await delete_message(id)
        return

    try: 
        info = a2s.info((str(ip), int(port) + 1))
    except Exception:
        info = ""
    try:
        online_name = re.findall("(?<=server_name=').*?(?=',)", str(info))[0] or ""
        map_name = re.findall("(?<=map_name=').*?(?=',)", str(info))[0] or ""
        mission_name = re.findall("(?<=game=').*?(?=',)", str(info))[0] or ""
        player_count = re.findall("(?<=player_count=).*?(?=,)", str(info))[0] or ""
        player_count_max = re.findall("(?<=max_players=).*?(?=,)", str(info))[0] or ""
        password_protected = re.findall("(?<=password_protected=).*?(?=,)", str(info))[0] or ""
        #Update server_name to the latest online_name found...
        await setup_message(id, channel_id, display_name, ip, port, online_name)
    except Exception:
        online_name = ""
        map_name = ""
        mission_name = ""
        player_count = ""
        player_count_max = ""
        password_protected=False


    
    server_info = interactions.Embed(
        title=online_name or server_name or display_name, 
        description=f"Currently playing `{mission_name}` on `{map_name}`." if info else "This server is currently offline, contact the @Server Admin should this be turned on.",
        color=interactions.Color.green() if info else interactions.Color.red(),
        #footer=interactions.EmbedFooter(text=f"Last Updated: {str(datetime.datetime.now())}"),
        timestamp=datetime.datetime.now()
        )

    #IP:PORT
    server_info.add_field("IP : PORT", value=f"{ip}:{port}", inline=True)

    #Player Field
    try:
        players = a2s.players((str(ip), int(port) + 1))
    except Exception:
        players = []
    if info:
        player_string = "" if players else "-"
        for player in players:
            player_string += str(re.findall("(?<=name=').*?(?=',)", str(player))[0]) + "\n"
        server_info.add_field(f"Online Players ({player_count}/{player_count_max})", value=player_string, inline=False)

    await message.edit("", embeds=server_info)

async def update_all():
    print(f"Updating all messages from guild: {1}")
    with open("messages.json", "r+") as f:
        jd = json.load(f)
        for k, v in jd.items():
            print(k,v)
            await update_status(k, v["channel_id"], v["display_name"], v["ip"], v["port"], v["server_name"])
            








#Bot Setup
@client.event
async def on_ready():
    print(f"We're online! We've logged in as {client.me.name}.")
    print(f"Our latency is {round(client.latency)} ms.")
    await update_all()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_all, 'interval', minutes=0.5, id="update_all")
    scheduler.start()


@client.command(
    name = "status_channel", 
    description = 'Setup a server info channel to be displayed in a specific category of your choosing.',
    options = [
        interactions.Option(
            name="display_name",
            description="This will be the display name of the channel",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="ip",
            description="The IP of the server to get a status from",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="port",
            description="The Port of the server to get a status from",
            type=interactions.OptionType.STRING,
            required=True,
        ),
        interactions.Option(
            name="mods_required",
            description="The direct link to the required mods preset",
            type=interactions.OptionType.STRING,
            required=False,
        ),
        interactions.Option(
            name="mods_clientside",
            description="The direct link to the clientside mods preset",
            type=interactions.OptionType.STRING,
            required=False,
        ),
    ]
)


async def create_status(ctx: interactions.CommandContext, display_name: str, ip: str, port: str, mods_required: str = "", mods_clientside: str = ""):
    guild = await ctx.get_guild()
    channel = await ctx.get_channel()
    message = await channel.send("Fetching server status....")
    await setup_message(str(message.id), str(channel.id), display_name, ip, port)
    

client.start()


