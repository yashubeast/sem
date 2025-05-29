import discord, os
from dotenv import load_dotenv

load_dotenv()

default_color = discord.Color.from_rgb(241, 227, 226)

ALLOWED_SERVERS = list(map(int, os.getenv("ALLOWED_SERVERS", "").split(",")))
def checkserver(ctx):
	return ctx.guild.id in ALLOWED_SERVERS

ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
def checkadmin(ctx):
	return ctx.author.id in ADMINS