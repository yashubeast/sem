from discord.ext import commands
import os

async def load_cog(bot, cog):
	await bot.load_extension(f"cogs.{cog}")

async def reload_cog(bot, cog):
	await bot.reload_extension(f"cogs.{cog}")

async def unload_cog(bot, cog):
	await bot.unload_extension(f"cogs.{cog}")

async def load_all_cogs(bot):
	for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			cog_name = filename[:-3]
			q_name = f"cogs.{cog_name}"
			try:
				await bot.unload_extension(q_name)
			except commands.ExtensionNotLoaded:
				pass
			await bot.load_extension(q_name)

async def reload_all_cogs(bot):
	for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			cog_name = filename[:-3]
			await bot.reload_extension(f"cogs.{cog_name}")

async def unload_all_cogs(bot, exclude=None):
	exclude = exclude or []
	exclude.append("admin")
	for filename in os.listdir("./cogs"):
		if filename.endswith(".py"):
			cog_name = filename[:-3]
			if cog_name not in exclude:
				await bot.unload_extension(f"cogs.{cog_name}")
	