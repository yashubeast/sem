import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

class misc(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# serverinfo
	@commands.hybrid_command(name="serverinfo", aliases=["svinfo"], help="info about the server")
	async def serverinfo(self, ctx):
		embed = discord.Embed(
			title=ctx.guild,
			color=discord.Color.from_rgb(241, 227, 226)
			)
		if ctx.guild.icon is not None:
			embed.set_thumbnail(url=ctx.guild.icon.url)
			# embed.set_author(icon_url=ctx.guild.icon.url)
		# embed.add_field(name="Server ID", value=ctx.guild.id)
		embed.add_field(name="Members", value=ctx.guild.member_count)
		embed.add_field(name="Channels", value=f"{len(ctx.guild.channels)}")
		embed.add_field(name=f"Roles", value=f"{len(ctx.guild.roles)}")
		# embed.set_footer(text=f"Created at: {ctx.guild.created_at}")
		
		await ctx.send(embed=embed)

	# sendembed cmd
	@commands.hybrid_command(name="sendembed", help="make the bot send custom embed")
	@app_commands.describe(
		title="title of the embed",
		description="description of the embed",
		fields="dynamic fields as 'name&value' pairs separated by | (pipes)",
		footer="Optional footer text",
		color="hex color (example #f1e3e2)"
	)
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
	await bot.add_cog(misc(bot))