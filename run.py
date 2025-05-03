import discord, os, asyncio, json
from discord.ext import commands
from dotenv import load_dotenv
from utils.cog_handler import load_all_cogs
from utils.status import update_status

load_dotenv()

bot = commands.Bot(command_prefix=",", help_command=None, intents=discord.Intents.all())

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}!")
	await update_status(bot)

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.MissingPermissions):
		await ctx.send("your aah lacks perms to use this cmd")
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send(">>> missing a required arg\n-# deleting..", delete_after=3)
	elif isinstance(error, commands.BotMissingPermissions):
		await ctx.send("i lack perms for ts :wilted:")
	elif isinstance(error, FileNotFoundError):
		await ctx.send("contact yasu, json file not found")
	elif isinstance(error, json.JSONDecodeError):
		await ctx.send("contact yasu, error reading json file")
	elif isinstance(error, commands.CommandNotFound):
		return
	else:
		await ctx.send(f":warning: error :warning: contact yasu ```py\n{error}```")

async def main():
	async with bot:
		await load_all_cogs(bot)
		await bot.start(os.getenv("TOKEN"))

asyncio.run(main())