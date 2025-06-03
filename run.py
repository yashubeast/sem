import discord, os, asyncio
from discord.ext import commands
from dotenv import load_dotenv
from utils.cog_handler import load_all_cogs
from utils.status import update_status
from utils.handlers.error import handle_command_error
from utils import database

load_dotenv()

bot = commands.Bot(command_prefix=",", help_command=None, intents=discord.Intents.all())

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}!")
	await update_status(bot)

@bot.event
async def on_command_error(ctx, error):
	await handle_command_error(ctx, error)

async def main():
	async with bot:
		await database.init_db(bot)
		await load_all_cogs(bot)
		await bot.start(os.getenv("TOKEN"))
	await bot.db.close()

asyncio.run(main())