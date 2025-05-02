import discord, asyncio
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

class emoji(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# emoji (group)
	@commands.hybrid_group(help="tools for managing emojis")
	@commands.has_permissions(administrator=True)
	async def emoji(self, ctx):
		if ctx.invoked_subcommand is None:
			pass

	# emoji list
	@emoji.command(name="list", help="list all emoji accessible by bot")
	async def list(self, ctx):
		emojis = [str(emoji) for guild in self.bot.guilds for emoji in guild.emojis]

		chunk = ""
		for emoji in emojis:
			if len(chunk) + len(emoji) + 1 > 2000:
				await ctx.send(chunk)
				chunk = ""
			chunk += emoji + " "

		await ctx.send(chunk)

async def setup(bot):
	await bot.add_cog(emoji(bot))