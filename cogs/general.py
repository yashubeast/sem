import discord
from discord.ext import commands
from discord import app_commands
from utils.values import default_color
from utils.help_handler import format_command_fields, helpview

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
	@commands.hybrid_command(name="help", help="wikipedia of bot", with_app_command=True)
	# @app_commands.describe(search="specify a category or a command to look up, or * for all commands in all categories")
	async def help(self, ctx):

		# check for cog
		# selected_cog_name = search.lower() if search else "general"
		# cog = self.bot.get_cog(selected_cog_name)
		# if cog:
			# embed = generate_help_embed(cog)

		embed = discord.Embed(
			title="wikipedia",
			description="commands starting:\nwith `,` are *prefix-cmd only*\nwith `/` are *app-cmd only*\nwith `nothing` are both prefix and app cmd",
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

async def setup(bot):
	await bot.add_cog(general(bot))