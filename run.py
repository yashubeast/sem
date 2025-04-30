import discord, os, asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
bot = commands.Bot(command_prefix=",", help_command=None, intents=discord.Intents.all())
disabled_cogs = []

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}!")
	await bot.change_presence(
		activity=discord.Activity(
			type=discord.ActivityType.playing, # .listening / .watching / .competing
			name="i/ mA LalIve"
		),
		status=discord.Status.online
	)

async def load():
	for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			cog_name = filename[:-3]
			if cog_name not in disabled_cogs:
				await bot.load_extension(f"cogs.{cog_name}")

async def main():
	async with bot:
		await load()
		await bot.start(os.getenv("TOKEN"))
asyncio.run(main())