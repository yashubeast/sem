import discord, os, asyncio, json
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

with open("assets/config.json", "r") as f:
	config = json.load(f)

bot = commands.Bot(command_prefix=config["main"]["prefix"], help_command=None, intents=discord.Intents.all())
bot.config = config

disabled_cogs = []

@bot.event
async def on_ready():
	print(f"Logged in as {bot.user}!")

	# get activity_type from config.json
	activity_type_str = bot.config["main"]["activity_type"].lower()
	activity_type_map = {
        "playing": discord.ActivityType.playing,
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching,
        "competing": discord.ActivityType.competing,
        "streaming": discord.ActivityType.streaming
	}
	activity_type = activity_type_map.get(activity_type_str, discord.ActivityType.playing)

	await bot.change_presence(
		activity=discord.Activity(
			type=activity_type, # .listening / .watching / .competing / .streaming
			name=bot.config["main"]["activity"]
		),
		status=discord.Status.online
	)

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.MissingPermissions):
		await ctx.send("your aah lacks perms to use this cmd")
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send("missing a required arg\n-# deleting..", delete_after=3)
	elif isinstance(error, commands.CommandNotFound):
		return
	else:
		await ctx.send(f":warning: error :warning: contact yasu ```py\n{error}```")

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