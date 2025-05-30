import discord, asyncio, re, aiohttp
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from utils.values import checkadmin

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
	
	@emoji.command(name="info", help="info on emoji slots in servers")
	async def info(self, ctx, *, servers: str):
		inputs = [s.strip() for s in servers.split(",")]
		results = []

		# emoji limits by nitro level
		tier_limits = {
			0: 50,
			1: 100,
			2: 150,
			3: 250
		}

		for identifier in inputs:
			guild = None

			# try to get by id
			if identifier.isdigit():
				guild = discord.utils.get(self.bot.guilds, id=int(identifier))

			# try to get by name
			if not guild:
				guild = discord.utils.find(lambda g: g.name.lower() == identifier.lower(), self.bot.guilds)

			if not guild:
				results.append(f"> server named `{identifier}` not found")
				continue

			limit = tier_limits.get(guild.premium_tier, 50)
			emojis = guild.emojis
			static_count = sum(not e.animated for e in emojis)
			animated_count = sum(e.animated for e in emojis)

			await ctx.send(
				f">>> {guild.name} (tier {guild.premium_tier}): free slots\n"
				f"- static: {limit - static_count}/{limit}\n"
				f"- animated: {limit - animated_count}/{limit}"
			)

	# emoji list
	@emoji.command(name="list", help="list all emojis accessible by bot")
	async def list(self, ctx, *, location: str = None):
		emojis = []

		if not location:
			return await ctx.send(">>> use argument `bot` to list bot's global emojis\n`all` to list all emojis from all servers\nor a comma separated list of server names to list emojis from those servers")

		if location.lower() == "bot":
			try:
				emojis = await self.bot.fetch_application_emojis()
			except discord.HTTPException:
				return await ctx.send(">>> failed to fetch bot's global emojis")
			if not emojis:
				return await ctx.send(">>> no global emojis found for the bot")

		elif location.lower() == "all":
			emojis = [str(emoji) for guild in self.bot.guilds for emoji in guild.emojis]
		
		else:
			server_names = [name.strip().lower() for name in location.split(",")]
			matched_guilds = [guild for guild in self.bot.guilds if guild.name.lower() in server_names]

			if not matched_guilds:
				return await ctx.send(">>> no matching servers found")

			emojis = [str(emoji) for guild in matched_guilds for emoji in guild.emojis]

			if not emojis:
				return await ctx.send(">>> no emojis found")

		# split and send in chunks to avoid 2000 char limit
		chunk = ""
		for emoji in emojis:
			emoji_str = str(emoji)
			if len(chunk) + len(emoji_str) + 1 > 2000:
				await ctx.send(chunk)
				chunk = ""
			chunk += emoji_str + " "

		if chunk:
			await ctx.send(chunk)

	# emoji import
	@emoji.command(name="import", help="import replied msg's emojis to server")
	@commands.has_permissions(manage_emojis_and_stickers=True)
	@commands.bot_has_permissions(manage_emojis_and_stickers=True)
	async def eimport(self, ctx, location: str = None):

		# ensure admin if location provided
		if location:
			if location.lower() == "bot":
				if not checkadmin(ctx):return await ctx.send(">>> yo aah ain't sem's admin for ts :wilted_rose:")
				target = self.bot.create_application_emoji

			else:
				try:
					if not location.isdigit():return await ctx.send(">>> invalid server id")
					target_guild = self.bot.get_guild(int(location))
					if not target_guild:return await ctx.send(">>> invalid server id")
				except ValueError:return await ctx.send(">>> invalid server id")

				# check if user is a member of that guild
				member = target_guild.get_member(ctx.author.id)
				if not member:return await ctx.send(">>> you are NOT a member of that server")
				if not member.guild_permissions.manage_emojis_and_stickers:return await ctx.send(">>> your aah lacks perms in specified server to use this cmd")
				bot_member = target_guild.get_member(self.bot.user.id)
				if not bot_member: return await ctx.send(">>> im not even in that server ???")
				if not bot_member.guild_permissions.manage_emojis_and_stickers:return await ctx.send(">>> i lack perms in that server :broken_heart:")

				target = target_guild.create_custom_emoji
		else:
			target = ctx.guild.create_custom_emoji

		# ensure theres a reply msg
		if not ctx.message.reference:return await ctx.send(">>> reply to a message with the emoji(s) to be imported\nadd optional argument server_id to specify server to import emojis to")

		# fetch replied message
		replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
		content = replied_message.content

		# match custom emoji (static and animated)
		matches = re.findall(r'<(a?):(\w+):(\d+)>', content)
		# return if no emojis in replied msg
		if not matches:return await ctx.send(">>> no custom emojis found in replied message")

		successfully_added = 0

		for index, (animated, name, emoji_id) in enumerate(matches, start=1):
			emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if animated else 'png'}"

			embed = discord.Embed(
				title=f"emoji {index}/{len(matches)}",
				description=f"type `skip` to skip emoji\ntype `cancel` to terminate import\n\ndefault name: `{name}`\nenter a name to save this emoji as:",
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
					await ctx.send(f">>> invalid name `{new_name}` use 2-32 characters, letters, numbers, and underscores only\n-# deleting..", delete_after=3)
					continue

				# fetch emoji image from CDN
				async with aiohttp.ClientSession() as session:
					async with session.get(emoji_url) as resp:
						if resp.status != 200:
							await ctx.send(f">>> failed to fetch emoji from url: {emoji_url}")
						image_data = await resp.read()
				
				# upload emoji to guild
				try:
					new_emoji = await target(name=new_name, image=image_data)
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