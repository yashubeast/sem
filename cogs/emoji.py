import discord, asyncio, re, aiohttp
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

default_color = discord.Color.from_rgb(241, 227, 226)

class emoji(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# emoji (group)
	@commands.group(help="tools for managing emojis")
	@commands.has_permissions(administrator=True)
	async def emoji(self, ctx):
		if ctx.invoked_subcommand is None:
			pass

	# emoji list
	@emoji.command(name="list", help="list all emojis accessible by bot")
	async def list(self, ctx):
		emojis = [str(emoji) for guild in self.bot.guilds for emoji in guild.emojis]

		chunk = ""
		for emoji in emojis:
			if len(chunk) + len(emoji) + 1 > 2000:
				await ctx.send(chunk)
				chunk = ""
			chunk += emoji + " "

		await ctx.send(chunk)

	# emoji import as
	@emoji.command(name="import", help="import replied msg's content as emojis for prefix cmd")
	@commands.has_permissions(manage_emojis_and_stickers=True)
	@commands.bot_has_permissions(manage_emojis_and_stickers=True)
	async def eimport(self, ctx):

		# ensure theres a reply msg
		if not ctx.message.reference:return await ctx.send("reply to a message with the emoji to be imported")

		# fetch replied message
		replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
		content = replied_message.content

		# match custom emoji (static and animated)
		matches = re.findall(r'<(a?):(\w+):(\d+)>', content)
		# return if no emojis in replied msg
		if not matches:return await ctx.send("no custom emojis found in replied message")

		successfully_added = 0

		for index, (animated, name, emoji_id) in enumerate(matches, start=1):
			emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"

			embed = discord.Embed(
				title=f"emoji {index}/{len(matches)}",
				description=f"type `skip` to skip emoji\ntype `cancel` to terminate import\n\ndefault name: `{name}`\nsend a name to save this emoji as:",
				color=default_color
			)
			embed.set_image	(url=emoji_url)

			if index == 1:
				prompt_msg = await ctx.send(embed=embed)
			else:
				await prompt_msg.edit(embed=embed)

			while True:

				try:
					user_msg = await self.bot.wait_for(
						"message",
						timeout=60.0,
						check=lambda m: m.author == ctx.author and m.channel == ctx.channel
				)
				except asyncio.TimeoutError:return await ctx.send("time out, import cancelled")

				user_input = user_msg.content.strip()
				await user_msg.delete()
				
				if user_input.lower() == "cancel":
					cancel_embed=discord.Embed(
						title="import cancelled", description=f"imported {successfully_added}/{len(matches)} emojis", color=default_color
						)
					await prompt_msg.edit(embed=cancel_embed)
					return
				if user_input.lower() == "skip":
					break

				new_name = user_input.replace(" ", "_")

				if not re.fullmatch(r"[A-Za-z0-9_]{2,32}", new_name):
					await ctx.send(f"invalid name `{new_name}` use 2-32 characters, letters, numbers, and underscores only\n-# deleting..", delete_after=3)
					continue

				# fetch emoji image from CDN
				async with aiohttp.ClientSession() as session:
					async with session.get(emoji_url) as resp:
						if resp.status != 200:
							await ctx.send(f"failed to fetch emoji from url: {emoji_url}")
						image_data = await resp.read()
				
				# upload emoji to guild
				try:
					new_emoji = await ctx.guild.create_custom_emoji(name=new_name, image=image_data)
					await ctx.send(f"emoji `{new_emoji.name}` added: {str(new_emoji)}\n-# deleting..", delete_after=3)
					successfully_added += 1
					break
				except discord.HTTPException as e:
					await ctx.send(f"failed to add emoji (emoji capacity exceeded probably): {e}")
					return
			
		end_embed=discord.Embed(
			title="import complete",
			description=f"imported {successfully_added}/{len(matches)} emojis",
			color=default_color
			)
		await prompt_msg.edit(embed=end_embed)

async def setup(bot):
	await bot.add_cog(emoji(bot))