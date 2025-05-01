import discord, asyncio
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

default_color = discord.Color.from_rgb(241, 227, 226)

def format_date_with_suffix(date):
	day = date.day
	suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
	return date.strftime(f"{day}{suffix} %b, %Y").lower()

def time_ago(date):
	now = datetime.now(timezone.utc)
	delta = relativedelta(now, date)

	parts = []

	if delta.years:
		parts.append(f"{delta.years} year{'s' if delta.years != 1 else ''}")
	if delta.months:
		parts.append(f"{delta.months} month{'s' if delta.months != 1 else ''}")
	if delta.days:
		parts.append(f"{delta.days} day{'s' if delta.days != 1 else ''}")

	return f"({', '.join(parts)} ago)" if parts else "(today)"

class info(commands.Cog):
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
		embed.add_field(name=f"created on", value=f"{format_date_with_suffix(guild.created_at)}\n-# {time_ago(guild.created_at)}", inline=False)
		
		await ctx.send(embed=embed)

	# info user
	@info.command(name="user", help="info on specified user")
	@app_commands.describe(user="user to look info on, provide any one: mention, user_id, display name, nickname, unique name")
	async def user(self, ctx, user: discord.User = None):
		user = user or ctx.author # default to command initiator if not user given
		member = ctx.guild.get_member(user.id)
		embed = discord.Embed(
			title=f"{user.name} ({user.display_name})",
			color=default_color,
		)

		embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
		# embed.add_field(name="top role", value=f"{member.top_role}")
		embed.add_field(name="roles", value=f"{len(member.roles)}", inline=False)
		embed.add_field(name="joined on", value=f"{format_date_with_suffix(member.joined_at)}\n-# {time_ago(member.joined_at)}")
		embed.add_field(name=f"created on", value=f"{format_date_with_suffix(user.created_at)}\n-# {time_ago(user.created_at)}")

		await ctx.send(embed=embed)

	# test command
	@commands.command(name="test")
	@commands.has_permissions(administrator=True)
	async def test(self, ctx, user: discord.User, channel:discord.TextChannel = None):
		await ctx.message.delete()
		channel = channel or ctx.channel

		await ctx.send(f"counting messages from {user.mention} in {channel.mention}... might take a while")

		count = 0
		checked = 0

		try:
			async for message in channel.history(limit=None, oldest_first=True):
				checked += 1
				if message.author.id == user.id:
					count += 1

				print(f"checked {checked} msgs, found {count}")

				await asyncio.sleep(0.01)

		except discord.Forbidden:
			await ctx.send("missing `read message history` permission")
			return
		except discord.HTTPException as e:
			await ctx.send(f"hit the rate limit lmfao: ```py\n{e}```")
			return
		
		await ctx.send(f"{user.mention} has **{count}** messages in {channel.mention}")

async def setup(bot):
	await bot.add_cog(info(bot))