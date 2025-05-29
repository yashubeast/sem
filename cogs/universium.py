import discord, aiosqlite
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from utils.json_handler import json_load, json_save

class universium(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
		self.bot.db = await aiosqlite.connect("assets/main.db")
	
	####
	####
	#### dynamic vc
	####
	####

	# listener for dynamic vc
	@commands.Cog.listener()
	async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
		if before.channel == after.channel:return

		data = json_load("dynamicvc")
		enabled_vcs = data.setdefault("enabled_vcs", {})

		# gather unique vcs involved in event
		affected_channels = {before.channel, after.channel}

		for vc in affected_channels:
			if not vc or str(vc.id) not in enabled_vcs:
				continue

		guild = vc.guild
		everyone = guild.default_role
		current_overwrite = vc.overwrites_for(everyone)
		member_count = len(vc.members)

		# Toggle visibility based on member count
		if member_count == 0 and current_overwrite.view_channel is not False:
			# no one left in vc
			current_overwrite.view_channel = False
			await vc.set_permissions(everyone, overwrite=current_overwrite)

		elif member_count > 0 and current_overwrite.view_channel != True:
			# someone joined vc
			current_overwrite.view_channel = True
			await vc.set_permissions(everyone, overwrite=current_overwrite)

	# dynamicvc
	@commands.hybrid_command(help="toggle dynamic vc", aliases=["dvc"])
	@commands.has_permissions(administrator=True)
	async def dynamicvc(self, ctx, channel: discord.VoiceChannel = None):
		data = json_load("dynamicvc")
		enabled = data.setdefault("enabled_vcs", {})

		if channel is None:
			channel = ctx.author.voice.channel if ctx.author.voice else None
			if channel is None:
				# await ctx.send("either specify a voice channel or be in one")

				guild_vcs = []

				for ch in enabled:
					vc = ctx.guild.get_channel(int(ch))
					if vc:
						guild_vcs.append(f"- {vc.mention}")

				if guild_vcs:
					await ctx.send(">>> dynamic vcs:\n" + "\n".join(guild_vcs))
				else:
					await ctx.send(">>> no dynamic vcs")

				return

		channel_id = str(channel.id)

		if channel_id in enabled:
			del enabled[channel_id]
			await channel.set_permissions(ctx.guild.default_role, overwrite=None)
			await ctx.send(f"disabled dynamicvc for {channel.mention}")
		else:
			enabled[channel_id] = True
			overwrite = channel.overwrites_for(ctx.guild.default_role)
			if len(channel.members) == 0:
				# hide channel if empty
				overwrite.view_channel = False
			else:
				# show channel if not empty
				overwrite.view_channel = True
			
			await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

			await ctx.send(f"enabled dynamicvc for {channel.mention}")
		
		json_save("dynamicvc", data)

	####
	####
	#### vc status
	####
	####

	# vc status
	# self.role_name = "In VC"  # change to your VC indicator role name
	# @commands.Cog.listener()
	# async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
	# 	guild = member.guild
	# 	async with db.execute("SELECT role_id FROM autoroles WHERE guild_id = ?", (guild.id,)) as cursor:
	# 		row = await cursor.fetchone()
	# 		if row:
	# 			role_id = int(row[0])
	# 			return guild.get_role(role_id)
	# 		return None
	# 	role = guild.get_role(self.role_id)
	# 	if not role:
	# 		return  # role doesn't exist

	# 	# user joined a vc
	# 	if not before.channel and after.channel:
	# 		if role not in member.roles:
	# 			await member.add_roles(role, reason="user joined a vc")

	# 	# user left vc
	# 	elif before.channel and not after.channel:
	# 		if role in member.roles:
	# 			await member.remove_roles(role, reason="user left all vcs")

async def setup(bot):
	await bot.add_cog(universium(bot))