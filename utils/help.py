from discord.ui import View, Button
from discord.ext import commands
from discord import app_commands
import discord, os, inspect
from utils.values import default_color

class cogbutton(Button):
	def __init__(self, label, cogs):
		super().__init__(label=label, style=discord.ButtonStyle.secondary)
		self.cogs = cogs
		self.index = 0

	async def callback(self, interaction: discord.Interaction):
		
		self.view.active_button = self

		self.view.left.disabled = False
		self.view.right.disabled = False

		embed = generate_help_embed([self.cogs[self.index]], title=f"{self.label} category")
		embed.set_footer(text=f"{self.index + 1}/{len(self.cogs)}")

		await interaction.response.edit_message(embed=embed, view=self.view)

class helpview(View):
	def __init__(self, bot):
		super().__init__(timeout=60)
		self.bot = bot
		self.active_button = None
		
		self.left = Button(label="<", style=discord.ButtonStyle.primary, row=0)
		self.right = Button(label=">", style=discord.ButtonStyle.primary, row=0)

		self.left.disabled = True
		self.right.disabled = True

		self.left.callback = self.go_left
		self.right.callback = self.go_right

		self.add_item(self.left)
		self.add_item(self.right)

		folders = get_cogs_by_folder(bot)
		for folder, fcogs in folders.items():
			self.add_item(cogbutton(label=folder, cogs=fcogs))
		
	async def go_left(self, interaction: discord.Interaction):
		btn = self.active_button
		if btn:
			btn.index = (btn.index -1) % len(btn.cogs)
			cog_name = btn.cogs[btn.index].qualified_name.split(".")[-1]
			embed = generate_help_embed(
				[btn.cogs[btn.index]],
				title=f"{btn.label} category"
			)
			embed.description = f"{cog_name} commands:"
			embed.set_footer(text=f"{btn.index + 1}/{len(btn.cogs)}")
			await interaction.response.edit_message(embed=embed, view=self)
		else:
			await interaction.response.send_message(">>> no category selected", ephemeral=True)
	
	async def go_right(self, interaction: discord.Interaction):
		btn = self.active_button
		if btn:
			btn.index = (btn.index + 1) % len(btn.cogs)
			cog_name = btn.cogs[btn.index].qualified_name.split(".")[-1]
			embed = generate_help_embed(
				[btn.cogs[btn.index]],
				title=f"{btn.label} category"
			)
			embed.description = f"{cog_name} commands:"
			embed.set_footer(text=f"{btn.index + 1}/{len(btn.cogs)}")
			await interaction.response.edit_message(embed=embed, view=self)
		else:
			await interaction.response.send_message(">>> no category selected", ephemeral=True)

def get_cogs_by_folder(bot):
	folders = {}

	for cog in bot.cogs.values():
		try:
			path = inspect.getfile(cog.__class__)
			rel_path = os.path.relpath(path, "cogs")
			parts = rel_path.split(os.sep)

			if len(parts) > 1:
				folder = parts[0]

			folders.setdefault(folder, []).append(cog)
		except Exception as e:
			print(f"error processing cog {cog.__class__.__name__}: {e}")

	return folders

def generate_help_embed(cogs: list[commands.Cog], title: str = None) -> discord.Embed:
	embed = discord.Embed(color=default_color)

	if title:
		embed.title = title

	for cog in cogs:
		commands_list = cog.get_commands()
		if not commands_list:
			continue

		formatted = format_command_fields(commands_list)
		if not formatted:
			continue

		cog_label = cog.qualified_name.split(".")[-1]
		embed.description = f"{cog_label} commands:"

		for name, desc in formatted:
			embed.add_field(name=name, value=f"-# {desc}", inline=False)
	
	if not embed.fields:
		embed.description = "no commands found"

	return embed

def format_command_fields(commands_list, prefix="", depth=None):
	fields = []
	for cmd in commands_list:

		if cmd.hidden:continue

		if isinstance(cmd, commands.HybridGroup):
			cmdprefix = ""
		elif isinstance(cmd, commands.HybridCommand):
			cmdprefix = ""
		elif isinstance(cmd, commands.Command):
			cmdprefix = ","
		elif isinstance(cmd, app_commands.Command):
			cmdprefix = "/"
		else:
			cmdprefix = ""

		params = list(cmd.clean_params.values())
		if params:
			params_str = "<" + ", ".join(p.name for p in params) + ">"
		else:
			params_str = ""

		not_full_name = f"{cmdprefix if depth == None else ''}{prefix + ' ' if prefix else ''}{cmd.name}".strip()
		full_name = f"{cmdprefix if depth == None else ''}{prefix + ' ' if prefix else ''}{cmd.name} {params_str}".strip()
		description = (cmd.help or "no description").partition('\n')[0]
		fields.append((full_name, description))

		if isinstance(cmd, commands.Group):
			sub_fields = format_command_fields(cmd.commands, prefix=not_full_name, depth=1)
			fields.extend(sub_fields)
	return fields