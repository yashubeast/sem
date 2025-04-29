import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

class admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	async def on_command_error(self, ctx, error):
		await ctx.reply(error, ephemeral = True)

	# sync cmd
	@commands.hybrid_command(
			name="sync",
			help="sync app commands",
			with_app_command=True
	)
	@app_commands.describe(scope="The scope of the sync global/guild")
	@commands.has_permissions(administrator=True)
	async def sync(self, ctx:Context, scope: str = "guild") -> None:
		if scope == "global":
			await ctx.bot.tree.sync()
			embed = discord.Embed(
				description="Slash commands have been globally synchronized.",
				color=0xBEBEFE
			)
			await ctx.send(embed=embed)
			return
		elif scope == "guild":
			ctx.bot.tree.copy_global_to(guild=ctx.guild)
			await ctx.bot.tree.sync(guild=ctx.guild)
			embed = discord.Embed(
				description="Slash commands have been synchronized in this guild.",
				color=0xBEBEFE
			)
			await ctx.send(embed=embed)
			return
		embed = discord.Embed(
		description="The scope must be `global` or `guild`.",
			color=0xE02B2B
		)
		await ctx.send(embed=embed, ephemeral=True)

	# unsync
	@commands.command(name="unsync", help="unsync app commands")
	@app_commands.describe(scope="The scope of the sync. Can be `global`, `current_guild` or `guild`")
	@commands.has_permissions(administrator=True)
	async def unsync(self, context: Context, scope: str = "guild") -> None:

		if scope == "global":
			context.bot.tree.clear_commands(guild=None)
			await context.bot.tree.sync()
			embed = discord.Embed(
				description="Slash commands have been globally unsynchronized.",
				color=0xBEBEFE,
			)
			await context.send(embed=embed)
			return
		elif scope == "guild":
			context.bot.tree.clear_commands(guild=context.guild)
			await context.bot.tree.sync(guild=context.guild)
			embed = discord.Embed(
				description="Slash commands have been unsynchronized in this guild.",
				color=0xBEBEFE,
			)
			await context.send(embed=embed)
			return
		embed = discord.Embed(
			description="The scope must be `global` or `guild`.", color=0xE02B2B
		)
		await context.send(embed=embed)

	# say cmd
	@commands.hybrid_command(name="say", help="make bot send a message")
	@app_commands.describe(message="The message to be repeated by the bot")
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def say(self, ctx:Context, *, message: str) -> None:
		await ctx.send(message)
		await ctx.message.delete()

async def setup(bot):
	await bot.add_cog(admin(bot))