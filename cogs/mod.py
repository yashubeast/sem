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

	# role
	@commands.hybrid_command(name="role", help="manage user roles", aliases=["r"])
	@commands.has_permissions(manage_roles=True)
	@commands.bot_has_permissions(manage_roles=True)
	async def role(self, ctx, member: discord.Member, role: discord.Role, *, reason: str = None):
		try:
			if role in member.roles:
				await member.remove_roles(role)
				await ctx.send(f">>> {role.name} removed from {member.nick or member.display_name or member.name} {reason if reason else ''}")
				try:await ctx.message.delete()
				finally:return

			await member.add_roles(role)
			await ctx.send(f">>> {role.name} given to {member.nick or member.display_name or member.name} {reason if reason else ''}")

			try:await ctx.message.delete()
			finally:return

		finally:
			try:await ctx.message.delete()
			finally:return

	# delete command	
	@commands.command(name="delete", aliases = ["d", "del"], help="purge messages")
	@commands.has_permissions(manage_messages=True)
	@commands.bot_has_permissions(manage_messages=True)
	@app_commands.describe(amount="amount of messages to purge")
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