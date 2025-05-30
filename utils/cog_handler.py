from discord.ext import commands
import os

async def load_cog(bot, cog):
	await bot.load_extension(f"cogs.{cog}")

async def reload_cog(bot, cog):
	await bot.reload_extension(f"cogs.{cog}")

async def unload_cog(bot, cog):
	await bot.unload_extension(f"cogs.{cog}")

async def load_all_cogs(bot):
	for root, _, files in os.walk("./cogs"):
		for file in files:
			if file.endswith(".py"):
				# get module path, e.g. cogs/admin/mod.py -> cogs.admin.mod
				rel_path = os.path.relpath(os.path.join(root, file), ".")
				module_path = rel_path[:-3].replace(os.path.sep, ".")

				try:
					await bot.unload_extension(module_path)
				except commands.ExtensionNotLoaded:
					pass
				await bot.load_extension(module_path)

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
	