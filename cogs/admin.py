import discord, traceback
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from utils.cog_handler import *

class admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	async def on_command_error(self, ctx, error):
		await ctx.reply(error, ephemeral = True)

	# sync cmd
	@commands.hybrid_command(name="sync", help="sync app commands", with_app_command=True)
	@app_commands.describe(query="target of the sync: global or guild")
	@commands.has_permissions(administrator=True)
	async def sync(self, ctx:Context, query: str = "guild") -> None:
		query = query.lower()
		if query == "global":
			await ctx.bot.tree.sync()
			await ctx.send("slash commands globally synchronized")
			return
		elif query == "guild":
			ctx.bot.tree.copy_global_to(guild=ctx.guild)
			await ctx.bot.tree.sync(guild=ctx.guild)
			await ctx.send("slash commands synchronized in current server")
			return
		await ctx.send("query must be global or guild", ephemeral=True)

	# unsync
	@commands.command(name="unsync", help="unsync app commands")
	@app_commands.describe(query="target of the sync: global or guild")
	@commands.has_permissions(administrator=True)
	async def unsync(self, ctx: Context, query: str = "guild") -> None:
		query = query.lower()
		if query == "global":
			ctx.bot.tree.clear_commands(guild=None)
			await ctx.send("slash commands globally unsynchronized")
			return
		elif query == "guild":
			ctx.bot.tree.clear_commands(guild=ctx.guild)
			await ctx.send("slash commands unsynchronized in current server")
			return
		await ctx.send("query must be global or guild")

	# re-sync
	@commands.command(name="resync", help="re-sync app commands")
	@app_commands.describe(query="target of the re-sync: global or guild")
	@commands.has_permissions(administrator=True)
	async def resync(self, ctx: Context, query: str = "guild") -> None:
		query = query.lower()
		if query == "global":
			ctx.bot.tree.clear_commands(guild=None)
			await ctx.bot.tree.sync()
			await ctx.send("slash commands globally re-synchronized")
			return
		elif query == "guild":
			ctx.bot.tree.clear_commands(guild=ctx.guild)
			await ctx.bot.tree.sync(guild=ctx.guild)
			await ctx.send("slash commands re-synchronized in current server")
			return
		await ctx.send("query must be global or guild")

	# cog
	@commands.hybrid_command(name="cog", help="load/unload/reload cogs")
	@app_commands.describe(action="list, load, unload, reload", cog="cog name, * for all")
	@commands.has_permissions(administrator=True)
	async def cog(self, ctx, action: str = None, cog: str = None):
		if not action or action.lower() == "list":
			cogs_list = ", ".join(sorted([extension.split('.')[-1] for extension in self.bot.cogs]))
			await ctx.send(f"> {cogs_list}")
			return

		action = action.lower()
		cog = cog.lower()
		
		try:
			if action in ("load", "l"):
				if cog == "*":
					await load_all_cogs(self.bot)
					await ctx.send(f"> loaded all cogs")
				else:
					await load_cog(self.bot, cog)
					await ctx.send(f"> loaded `{cog}`")
				return
			if action in ("reload", "r"):
				if cog == "*":
					await reload_all_cogs(self.bot)
					await ctx.send(f"> reloaded all cogs")
				else:
					await reload_cog(self.bot, cog)
					await ctx.send(f"> reloaded `{cog}`")
				return
			if action in ("unload", "u"):
				if cog == "*":
					await unload_all_cogs(self.bot)
					await ctx.send(f"unloaded all cogs, except admin")
				else:
					await unload_cog(self.bot, cog)
					await ctx.send(f"> unloaded `{cog}`")
				return

		except commands.ExtensionNotLoaded:
			await ctx.send(f"cog `{cog}` not loaded")

		except commands.ExtensionNotFound:
			await ctx.send(f"inexistent cog `{cog}`")
		
		except commands.ExtensionAlreadyLoaded:
			await ctx.send(f"cog `{cog}` already loaded")

		except Exception as e:
			await ctx.send(f"error `{cog}`\n```{traceback.format_exc()}```")

	# say cmd
	@commands.hybrid_command(name="say", help="make bot send a message")
	@app_commands.describe(message="the content to be repeated by the bot")
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def say(self, ctx:Context, *, message: str) -> None:
		await ctx.send(message)
		await ctx.message.delete()

	# sendembed cmd
	@commands.hybrid_command(name="sendembed", help="make the bot send custom embed")
	@app_commands.describe(
		title="title of the embed",
		description="description of the embed",
		fields="dynamic fields as 'name & value' pairs separated by | (pipes)",
		footer="optional footer text",
		color="hex color (example #f1e3e2)"
	)
	@commands.has_permissions(administrator=True)
	async def sendembed(
		self,
		ctx: Context,
		title: str = None,
		description: str = None,
		fields: str = None,
		footer: str = None,
		color: str = "#f1e3e2"
	):
		# Convert hex color string to int
		try:
			embed_color = int(color.strip("#"), 16)
		except ValueError:
			await ctx.reply("invalid color format, use hex like #f1e3w2", ephemeral=True)
			return

		embed = discord.Embed(
			title=title or None,
			description=description or None,
			color=embed_color
		)

		if fields:
			for field in fields.split("|"):
				if "&"in field:
					name, value = field.split("&", 1)
					embed.add_field(name=name.strip(), value=value.strip(), inline=False)

		if footer:
			embed.set_footer(text=f"{footer}")

		await ctx.send(embed=embed)

async def setup(bot):
	await bot.add_cog(admin(bot))