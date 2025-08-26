import discord
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from utils.values import default_color

async def format_date_with_suffix(date):
	day = date.day
	suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
	return date.strftime(f"{day}{suffix} %b, %Y").lower()

async def time_ago(date):
	now = datetime.now(timezone.utc)
	delta = relativedelta(now, date)

	parts = []

	if delta.years:
		parts.append(f"{delta.years}y")
	if delta.months:
		parts.append(f"{delta.months}m")
	if delta.days:
		parts.append(f"{delta.days}d")

	return f"({', '.join(parts)} ago)" if parts else "(today)"

async def info_servers(guilds):
	if guilds:
		guilds_str = "\n".join(f"[{g.name}](https://discord.com/channels/{g.id})" for g in guilds)
		message = f"### servers i am in: {len(guilds)}\n>>> " + guilds_str
	else:
		message = "> sem is not in any servers"
	return message

async def info_user(ctx, user):
		member = ctx.guild.get_member(user.id)
		embed = discord.Embed(
			title=f"{user.name} ({user.display_name})",
			color=default_color
		)

		embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
		# embed.add_field(name="top role", value=f"{member.top_role}")
		embed.add_field(name="roles", value=f"{len(member.roles)}", inline=False)
		embed.add_field(name="joined on", value=f"{await format_date_with_suffix(member.joined_at)}\n-# {await time_ago(member.joined_at)}")
		embed.add_field(name=f"created on", value=f"{await format_date_with_suffix(user.created_at)}\n-# {await time_ago(user.created_at)}")

		return embed

async def info_server(ctx):
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
		embed.add_field(name=f"created on", value=f"{await format_date_with_suffix(guild.created_at)}\n-# {await time_ago(guild.created_at)}", inline=False)
		
		return embed

async def info_role(ctx, role: discord.Role) -> discord.Embed:
	embed = discord.Embed(title=role.name, color=role.color)
	embed.add_field(name="members", value=len(role.members))
	embed.add_field(name="created on", value=f"{await format_date_with_suffix(role.created_at)}\n-# {await time_ago(role.created_at)}", inline=False)
	return embed

exceptions = {
	# 'cogs.fun.fun'
}