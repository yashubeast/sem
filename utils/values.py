import discord, os
from dotenv import load_dotenv

load_dotenv()

default_color = discord.Color.from_rgb(241, 227, 226)

def checkuni(ctx):
	return ctx.guild.id == 1222206531479666740

ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
def checkadmin(ctx):
	return ctx.author.id in ADMINS