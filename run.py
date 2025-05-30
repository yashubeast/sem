import discord, os, asyncio, json, aiosqlite
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
		await ctx.send(">>> your aah lacks perms to use this cmd")
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send(">>> missing a required arg\n-# deleting..", delete_after=3)
	elif isinstance(error, commands.BotMissingPermissions):
		await ctx.send(">>> i lack perms for ts :wilted_rose:")
	elif isinstance(error, FileNotFoundError):
		await ctx.send(">>> contact yasu, json file not found")
	elif isinstance(error, json.JSONDecodeError):
		await ctx.send(">>> contact yasu, error reading json file")
	elif isinstance(error, discord.Forbidden):
		await ctx.send(">>> contact yasu, bot lacks perms")
	elif isinstance(error, commands.CommandNotFound):
		return
	elif str(error).startswith("Role") and str(error).endswith("not found."):
		await ctx.send(f">>> role doesn't exist")
	else:
		if str(error).startswith("The check functions for command"):
			await ctx.send(">>> command not allowed for this aah server\n-# deleting..", delete_after=3)
		else:
			await ctx.send(f">>> :warning: error :warning: contact yasu ```py\n{error}```")

async def database():
	os.makedirs("assets", exist_ok=True)
	bot.db = await aiosqlite.connect("assets/main.db")
	await bot.db.execute("PRAGMA journal_mode=WAL")

	async with bot.db.cursor() as cursor:
		await cursor.execute("""
			CREATE TABLE IF NOT EXISTS tags(
				name TEXT,
				content TEXT,
				gid INT,
				cid INT
			)
		""")
		await cursor.execute("""
			CREATE TABLE IF NOT EXISTS servers(
			 	pos INTEGER UNIQUE,
				name TEXT UNIQUE,
				content TEXT
			)
		""")
		await cursor.execute("""
			CREATE TABLE IF NOT EXISTS servers_msgs(
			pos INTEGER PRIMARY KEY,
			mid TEXT NOT NULL
			)
		""")
	
	await bot.db.commit()

async def main():
	async with bot:
		await database()
		await load_all_cogs(bot)
		await bot.start(os.getenv("TOKEN"))
	await bot.db.close()

asyncio.run(main())