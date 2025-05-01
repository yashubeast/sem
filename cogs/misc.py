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

async def setup(bot):
	await bot.add_cog(misc(bot))