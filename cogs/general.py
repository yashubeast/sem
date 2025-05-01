import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from discord.ui import View, Select

default_color = discord.Color.from_rgb(241, 227, 226)

def format_command_tree(command, depth=0, is_last=True, prefix_stack=None, is_root=True):
    if prefix_stack is None:
        prefix_stack = []

    lines = []

    if is_root:
        # root command (no connector)
        description = (command.help or "no description").partition('\n')[0]
        lines.append(f"{command.name} - {description}")
    else:
        # child command (with tree prefix)
        connector = "└─" if is_last else "├─"
        prefix = "".join(prefix_stack) + connector
        description = (command.help or "no description").partition('\n')[0]
        lines.append(f"{prefix} {command.name} - {description}")

    # if it's a group, recurse through subcommands
    if isinstance(command, commands.Group):
        subcommands = command.commands
        count = len(subcommands)
        for idx, sub in enumerate(subcommands):
            is_sub_last = (idx == count - 1)
            new_stack = prefix_stack.copy()
            new_stack.append("│  " if not is_last else " ")
            lines.extend(format_command_tree(sub, depth + 1, is_last=is_sub_last, prefix_stack=new_stack, is_root=False))

    return lines

def format_commands(commands_list):
	all_lines = []
	for cmd in commands_list:
		all_lines.extend(format_command_tree(cmd))
	return "\n".join(all_lines) if all_lines else "no commands in this category"

def resolve_command_path(commands_list, path_parts):
    if not path_parts:
        return None
    for cmd in commands_list:
        if cmd.name.lower() == path_parts[0].lower():
            if len(path_parts) == 1:
                return cmd
            if isinstance(cmd, commands.Group):
                return resolve_command_path(cmd.commands, path_parts[1:])
    return None

class helpdropdown(Select):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		options = [
			discord.SelectOption(label=cog_name)
			for cog_name in bot.cogs
		]
		super().__init__(placeholder="choose a category", options=options)

	async def callback(self, interaction: discord.Interaction):
		cog = self.bot.get_cog(self.values[0])
		if cog is None:
			await interaction.response.send_message("category doesn't exist anymore", ephemeral=True)
			return

		commands_list = cog.get_commands()

		help_text = format_commands(commands_list)
		embed = discord.Embed(
			title=f"{cog.qualified_name} commands",
			description=f"```{help_text}```",
			color=default_color
		)
		await interaction.response.edit_message(embed=embed, view=self.view)

class helpview(View):
	def __init__(self, bot: commands.Bot):
		super().__init__(timeout=60)
		self.add_item(helpdropdown(bot))

class general(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# ping cmd
	@commands.hybrid_command(with_app_command=True, help="bot's latency")
	async def ping(self, ctx):
		await ctx.send(f"{round(self.bot.latency * 1000)}ms.", ephemeral=True)
	
	# help
	@commands.hybrid_command(name="help", help="wikipedia of bot", with_app_command=True)
	@app_commands.describe(search="specify a category or a command to look up, or * for all commands in all categories")
	async def help(self, ctx, *,search: str = None):
		if not search:
			cog = self.bot.get_cog("general") # initial cog to start the message with
			if cog:
				commands_list = cog.get_commands()

				help_text = format_commands(commands_list)
				embed = discord.Embed(
					title=f"{cog.qualified_name} commands",
					description=f"```{help_text}```",
					color=default_color
				)
				await ctx.send(embed=embed, view=helpview(self.bot), ephemeral=True)
			else:
				await ctx.send("contact admin (command broke lmfao)")
			return

		if search == "*":
			embed = discord.Embed(
				title="wikipedia",
				color=default_color
			)
			for i in self.bot.cogs:
				cog = self.bot.get_cog(i)
				commands_list= cog.get_commands()
				
				help_text = format_commands(commands_list)
				embed.add_field(
					name=cog.qualified_name, value=f"```{help_text}```", inline=False
				)
			await ctx.send(embed=embed, ephemeral=True)
			return

		# check for cog
		cog = self.bot.get_cog(search.lower())
		if cog:
			commands_list = cog.get_commands()
			
			help_text = format_commands(commands_list)
			embed = discord.Embed(
				title=f"{cog.qualified_name} commands",
				description=f"```{help_text}```",
				color=default_color
			)
			await ctx.send(embed=embed)
			return

		# check for command
		path_parts = search.split()
		for cog_name in self.bot.cogs:
			cog = self.bot.get_cog(cog_name)
			if not cog:
				continue
			found_command = resolve_command_path(cog.get_commands(), path_parts)
			if found_command:
				if isinstance(found_command, commands.Group):
					help_text = format_commands(found_command.commands)
					description = (found_command.help or '') + f"\n```{help_text}```"
				else:
					# normal command
					description = found_command.help or "no description"

				embed = discord.Embed(
					title=" ".join(path_parts),
					description=description,
					color=default_color
				)
				await ctx.send(embed=embed)
				return

		await ctx.send(f"no command or category named `{search}` found")

async def setup(bot):
	await bot.add_cog(general(bot))