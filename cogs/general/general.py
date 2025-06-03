import discord, asyncio
from discord.ext import commands
from utils.values import default_color
from utils.help import helpview
from utils.info import *

class general(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# ping cmd
	@commands.command(with_app_command=True, help="bot's latency")
	async def ping(self, ctx):
		await ctx.send(f"{round(self.bot.latency * 1000)}ms.")
	
	# help
	@commands.hybrid_command(name="help", help="wikipedia of bot")
	# @app_commands.describe(search="specify a category or a command to look up, or * for all commands in all categories")
	async def help(self, ctx):

		# check for cog
		# selected_cog_name = search.lower() if search else "general"
		# cog = self.bot.get_cog(selected_cog_name)
		# if cog:
			# embed = generate_help_embed(cog)

		embed = discord.Embed(
			title="wikipedia",
			description="commands starting with:\n`,` are *prefix-cmd only*\n`/` are *app-cmd only*\n`nothing` are both prefix and app-cmd",
			color=default_color
		)

		await ctx.send(embed=embed, view=helpview(self.bot), ephemeral=True)
		return

		# if search == "*":
		# 	embed = discord.Embed(
		# 		title="wikipedia",
		# 		color=default_color
		# 	)
		# 	for i in self.bot.cogs:
		# 		cog = self.bot.get_cog(i)
		# 		commands_list = cog.get_commands()
		# 		fields = format_command_fields(commands_list)

		# 		for name, desc in fields:
		# 			embed.add_field(name=name, value=desc, inline=False)

		# 	await ctx.send(embed=embed, ephemeral=True)
		# 	return

		# check for command
		# path_parts = search.split()
		# for cog_name in self.bot.cogs:
		# 	cog = self.bot.get_cog(cog_name)
		# 	if not cog:
		# 		continue
		# 	found_command = resolve_command_path(cog.get_commands(), path_parts)
		# 	if found_command:
		# 		if isinstance(found_command, commands.Group):
		# 			help_text = format_commands(found_command.commands)
		# 			description = (found_command.help or '') + f"\n{help_text}"
		# 		else:
		# 			# normal command
		# 			description = found_command.help or "no description"

		# 		embed = discord.Embed(
		# 			title=" ".join(path_parts),
		# 			description=description,
		# 			color=default_color
		# 		)
		# 		await ctx.send(embed=embed)
		# 		return
		# await ctx.send(f"no command or category named `{search}` found")

	# info
	@commands.hybrid_command(help="universal info cmd (server, user)", aliases=["i"])
	async def info(self, ctx, *, query: str = None):

		# info bot
		if not query:
			guilds = self.bot.guilds
			await ctx.send(await info_servers(guilds))
			return

		# parting
		parts = query.split()
		sent_ids = set()

		for part in parts:
			member = None

			# check for server
			if part.lower() == "server" and "server" not in sent_ids:
				embed = await info_server(ctx)
				await ctx.send(embed=embed)
				sent_ids.add("server")
				continue

			# check for @mention
			if part.startswith("<@") and part.endswith(">"):
				user_id = part.strip("<@!>")
				if user_id.isdigit():
					member = ctx.guild.get_member(int(user_id))
					if not member:
						try:
							member = await ctx.bot.fetch_user(int(user_id))
						except:
							pass
			
			# check for user id
			elif part.isdigit():
				member = ctx.guild.get_member(int(part))
				if not member:
					try:
						member = await ctx.bot.fetch_user(int(part))
					except:
						pass
			
			# try name or nick
			if not member:
				member = discord.utils.find(
					lambda m: part.lower() in (m.name.lower(), m.display_name.lower()),
					ctx.guild.members
				)

			# if checked and not already sent
			if member and member.id not in sent_ids:
				embed = await info_user(ctx, member)
				await ctx.send(embed=embed)
				sent_ids.add(member.id)
				continue
			
			# check for roles
			role = None
			if part.startswith("<@&") and part.endswith(">"):
				role_id = part.strip("<@&>")
				if role_id .isdigit():
					role = ctx.guild.get_role(int(role_id))
			
			elif part.isdigit():
				role = ctx.guild.get_role(int(part))
			
			if not role:
				role = discord.utils.find(
					lambda r: part.lower() in r.name.lower(),
					ctx.guild.roles
				)

			if role and role.id not in sent_ids:
				embed = await info_role(ctx, role)
				await ctx.send(embed=embed)
				sent_ids.add(role.id)
				continue

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
	await bot.add_cog(general(bot))