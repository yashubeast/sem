import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

class mod(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	# delete command	
	@commands.command(name="delete", aliases = ["d", "del"], help="purge messages")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def delete(self, cfx, amount: int = 1):
		await cfx.channel.purge(limit=amount+1)

	# # kick command
	# @app_commands.command()
	# @app_commands.checks.has_permissions(kick_members=True)
	# async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason=None):
	# 	await interaction.guild.kick(member)
	# 	await interaction.response.send_message(f"{member.mention} was kicked.")

	# # ban command
	# @app_commands.command()
	# @app_commands.checks.has_permissions(ban_members=True)
	# async def ban(self, interaction: discord.Interaction, member: discord.Member, *, reason=None):
	# 	await interaction.guild.ban(member)
	# 	await interaction.response.send_message(f"{member.mention} was banned.")

	# # unban commands
	# @app_commands.command()
	# @app_commands.checks.has_permissions(ban_members=True)
	# async def unban(self, interaction: discord.Interaction, user_id: str):
	# 	user = await self.bot.fetch_user(user_id)
	# 	await interaction.guild.unban(user)
	# 	await interaction.response.send_message(f"{user.name} was unbanned.")

async def setup(bot):
	await bot.add_cog(mod(bot))