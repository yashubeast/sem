import discord, os, asyncio, aiosqlite
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands

class general(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# ping cmd
	@commands.hybrid_command(with_app_command=True, help="sem's latency")
	async def ping(self, ctx):
		await ctx.send(f"{round(self.bot.latency * 1000)}ms.", ephemeral=True)
	
	# help command
	@commands.hybrid_command(help="sem-wiki", with_app_command=True)
	async def help(self, ctx):
		try:
			embed = discord.Embed(
				title="sem-wiki",
				color=discord.Color.from_rgb(241, 227, 226)
			)
			for i in self.bot.cogs:
				cog = self.bot.get_cog(i.lower())
				commands= cog.get_commands()
				data = []
				for command in commands:
					description = (command.help or "No description").partition("\n")[0]
					data.append(f"{command.name} - {description}")
				help_text = "\n".join(data)
				embed.add_field(
					name=i.capitalize(), value=f"```{help_text}```", inline=False
				)
			await ctx.send(embed=embed, ephemeral=True)
		except Exception as e:
			await ctx.send(f"error: {str(e)}")

	# @commands.hybrid_command(help="Show the help menu", with_app_command=True)
	# async def wikipedia(self, ctx):
	# 	try:
	# 		help_message = "sem-wiki\n\n"

	# 		for cog_name in self.bot.cogs:
	# 			cog = self.bot.get_cog(cog_name)
	# 			if not cog:
	# 				continue

	# 			entries = []
	# 			for command in cog.get_commands():
	# 				if isinstance(command, commands.Group):  # if it's a group command
	# 					group_info = f"**{command.name}** (Group)"
	# 					for subcommand in command.commands:
	# 						sub_desc = (subcommand.help or "No description").partition("\n")[0]
	# 						group_info += f"\n- {subcommand.name}: {sub_desc}"
	# 					entries.append(group_info)
	# 				else:
	# 					description = (command.help or "No description").partition("\n")[0]
	# 					entries.append(f"**{command.name}** - {description}")

	# 			help_text = "\n".join(entries) if entries else "No commands."
	# 			help_message += f"**{cog_name.capitalize()}**\n{help_text}\n\n"

	# 		await ctx.send(help_message.strip())

	# 	except Exception as e:
	# 		await ctx.send(f"Error: {str(e)}")

async def setup(bot):
	await bot.add_cog(general(bot))