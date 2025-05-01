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
	@app_commands.describe(query="target of the sync: global or guild")
	@commands.has_permissions(administrator=True)
	async def sync(self, ctx:Context, query: str = "guild") -> None:

		try:
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

		except Exception as e:
			await ctx.send(f"error: {e}")

	# unsync
	@commands.command(name="unsync", help="unsync app commands")
	@app_commands.describe(scope="target of the sync: global or guild")
	@commands.has_permissions(administrator=True)
	async def unsync(self, ctx: Context, query: str = "guild") -> None:

		try:
			if query == "global":
				ctx.bot.tree.clear_commands(guild=None)
				await ctx.bot.tree.sync()
				await ctx.send("slash commands globally unsynchronized")
				return
			elif query == "guild":
				ctx.bot.tree.clear_commands(guild=ctx.guild)
				await ctx.bot.tree.sync(guild=ctx.guild)
				await ctx.send("slash commands unsynchronized in current server")
				return
			await ctx.send("query must be global or guild")
		
		except Exception as e:
			await ctx.send(f"error: {e}")

	# say cmd
	@commands.hybrid_command(name="say", help="make bot send a message")
	@app_commands.describe(message="The message to be repeated by the bot")
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
		fields="dynamic fields as 'name&value' pairs separated by | (pipes)",
		footer="Optional footer text",
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