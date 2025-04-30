import discord, random
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands

class coinflip(discord.ui.View):
	def __init__(self) -> None:
		super().__init__()
		self.value=None
	
	@discord.ui.button(label="heads", style=discord.ButtonStyle.blurple)
	async def confirm(self, Interaction: discord.Interaction, button: discord.ui.Button) -> None:
		self.value = "heads"
		self.stop()

	@discord.ui.button(label="tails", style=discord.ButtonStyle.blurple)
	async def cancel(self, Interaction: discord.Interaction, button: discord.ui.Button) -> None:
		self.value = "tails"
		self.stop()

class fun(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	@commands.hybrid_command(name="coinflip", help="gamble your life away")
	async def coinflip(self, ctx: Context) -> None:
		buttons = coinflip()
		embed = discord.Embed(
			description="What is your bet ?",
			color=0xBEBEFE			
		)
		message = await ctx.send(embed=embed, view=buttons)
		await buttons.wait()
		result = random.choice(["heads", "tails"])
		if buttons.value == result:
			embed = discord.Embed(
				description=f"Correct! You guessed `{buttons.value}` and i flipped the coin to `{result}`.",
				color=0xBEBEFE
			)
		else:
			embed = discord.Embed(
				title="idiot"
			)
		await message.edit(embed=embed, view=None, content=None)

async def setup(bot):
	await bot.add_cog(fun(bot))