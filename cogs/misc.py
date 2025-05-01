import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

default_color = discord.Color.from_rgb(241, 227, 226)

def format_date_with_suffix(date):
	day = date.day
	suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
	return date.strftime(f"{day}{suffix} %b, %Y")

class misc(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# info (group)
	@commands.hybrid_group(help="tools for info and stats")
	async def info(eslf, ctx):
		if ctx.invoked_subcommand is None:
			pass

	# info server
	@info.command(name="server", help="info on current server")
	async def server(self, ctx):
		try:
			guild = ctx.guild
			embed = discord.Embed(
				title=guild.name,
				color=default_color
				)
			if guild.icon:
				embed.set_thumbnail(url=guild.icon.url)

			embed.add_field(name="members", value=guild.member_count)
			embed.add_field(name="channels", value=f"{len(guild.channels)}")
			embed.add_field(name=f"roles", value=f"{len(guild.roles)}")
			embed.set_footer(text=f"created at: {guild.created_at}") # crowded format to show info, fix this
			
			await ctx.send(embed=embed)
		
		except Exception as e:
			await ctx.send(f"error: {e}")

	# info user
	@info.command(name="user", help="info on specified user")
	async def user(self, ctx, user: discord.User = None):
		try:
			user = user or ctx.author # default to command initiator if not user given
			embed = discord.Embed(
				title=f"{user.name}#{user.discriminator}",
				color=default_color,
			)

			embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
			embed.add_field(name="created at", value=f"{format_date_with_suffix(user.created_at)}\n-# {user.created_at.strftime('%H: %M: %S')}")

			await ctx.send(embed=embed)

		except Exception as e:
			await ctx.send(f"error: {e}")

async def setup(bot):
	await bot.add_cog(misc(bot))