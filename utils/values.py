import discord, os
from dotenv import load_dotenv

load_dotenv()

default_color = discord.Color.from_rgb(241, 227, 226)

ALLOWED_SERVERS = [int(x) for x in os.getenv("ALLOWED_SERVERS", "").split(",") if x.strip()]
def checkserver(ctx):
	return ctx.guild.id in ALLOWED_SERVERS

ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
def checkadmin(ctx):
	return ctx.author.id in ADMINS