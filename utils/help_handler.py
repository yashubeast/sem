from discord.ui import View, Button
from discord.ext import commands
from discord import app_commands
import discord
from utils.values import default_color

class cogbutton(Button):
    def __init__(self, label, cog_name):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.cog_name = cog_name

    async def callback(self, interaction: discord.Interaction):
        # Example usage - you can adapt this
        cog = self.view.bot.get_cog(self.cog_name)
        if cog:
            embed = generate_help_embed(cog)
            for item in self.view.children:
                if isinstance(item, cogbutton):
                    item.disabled = (item.cog_name == self.cog_name)
            await interaction.response.edit_message(embed=embed, view=self.view)

class helpview(View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
        for cog_name in bot.cogs:
            self.add_item(cogbutton(label=cog_name, cog_name=cog_name))

def generate_help_embed(cog: commands.Cog, title: str = None) -> discord.Embed:
	commands_list = cog.get_commands()

	if not commands_list:
		embed = discord.Embed(
			title=title or f"{cog.qualified_name} commands",
			description="no commands in this category yet",
			color=default_color
		)
		return embed

	fields = format_command_fields(commands_list)

	embed = discord.Embed(
		title=title or f"{cog.qualified_name} commands",
		color=default_color
	)
	for name, desc in fields:
		embed.add_field(name=f"{name}", value=desc, inline=False)

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