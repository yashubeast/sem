from pyexpat.errors import messages
from typing import Any, Coroutine

import discord, traceback, asyncio, json, re, contextlib, io, sys, subprocess
from discord.ext.commands import Context
from discord import app_commands, Message
from utils.cog_handler import *
from utils.json_handler import json_load, json_save
from utils.status import update_status
from utils.values import checkadmin

class admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	# sync cmd
	@commands.command(name="sync", help="sync app commands", with_app_command=True)
	@commands.has_permissions(administrator=True)
	async def sync(self, ctx:Context, query: str = "guild") -> None:
		query = query.lower()
		if query == "global":
			await ctx.bot.tree.sync()
			await ctx.send("> slash commands globally synchronized")
			return
		elif query == "guild":
			ctx.bot.tree.copy_global_to(guild=ctx.guild)
			await ctx.bot.tree.sync(guild=ctx.guild)
			await ctx.send("> slash commands synchronized in current server")
			return
		await ctx.send("> query must be global or guild", ephemeral=True)

	# unsync
	@commands.command(name="unsync", help="unsync app commands")
	@app_commands.describe(query="target of the sync: global or guild")
	@commands.has_permissions(administrator=True)
	async def unsync(self, ctx: Context, query: str = "guild") -> None:
		query = query.lower()
		if query == "global":
			ctx.bot.tree.clear_commands(guild=None)
			await ctx.send("> slash commands globally unsynchronized")
			return
		elif query == "guild":
			ctx.bot.tree.clear_commands(guild=ctx.guild)
			await ctx.send("> slash commands unsynchronized in current server")
			return
		await ctx.send("> query must be global or guild")

	# re-sync
	@commands.command(name="resync", help="re-sync app commands")
	@app_commands.describe(query="target of the re-sync: global or guild")
	@commands.has_permissions(administrator=True)
	async def resync(self, ctx: Context, query: str = "guild") -> None:
		prompt = await ctx.send("> hollon..")
		query = query.lower()
		if query == "global":
			ctx.bot.tree.clear_commands(guild=None)
			await asyncio.sleep(5)
			await ctx.bot.tree.sync()
			await prompt.edit(content="> slash commands globally re-synchronized")
			return
		elif query == "guild":
			ctx.bot.tree.clear_commands(guild=ctx.guild)
			await asyncio.sleep(5)
			await ctx.bot.tree.sync(guild=ctx.guild)
			await prompt.edit(content="> slash commands re-synchronized in current server")
			return
		await prompt.edit(content="> query must be global or guild")

	# cog
	@commands.command(name="cog", help="load/unload/reload cogs")
	@commands.has_permissions(administrator=True)
	async def cog(self, ctx, action: str = None, cog: str = None):
		if not action or action.lower() == "list":
			cogs_list = ", ".join(sorted([extension.split('.')[-1] for extension in self.bot.cogs]))
			await ctx.send(f"> {cogs_list}")
			return

		action = action.lower()
		cog = cog.lower()
		
		try:
			if action in ("load", "l"):
				if cog == "*":
					await load_all_cogs(self.bot)
					await ctx.send(f"> loaded all cogs")
				else:
					await load_cog(self.bot, cog)
					await ctx.send(f"> loaded `{cog}`")
				return
			if action in ("reload", "r"):
				if cog == "*":
					await reload_all_cogs(self.bot)
					await ctx.send(f"> reloaded all cogs")
				else:
					await reload_cog(self.bot, cog)
					await ctx.send(f"> reloaded `{cog}`")
				return
			if action in ("unload", "u"):
				if cog == "*":
					await unload_all_cogs(self.bot)
					await ctx.send(f"unloaded all cogs, except admin")
				else:
					await unload_cog(self.bot, cog)
					await ctx.send(f"> unloaded `{cog}`")
				return

		except commands.ExtensionNotLoaded:
			await ctx.send(f"cog `{cog}` not loaded")

		except commands.ExtensionNotFound:
			await ctx.send(f"inexistent cog `{cog}`")
		
		except commands.ExtensionAlreadyLoaded:
			await ctx.send(f"cog `{cog}` already loaded")

		except Exception as e:
			await ctx.send(f"error `{cog}`\n```{traceback.format_exc()}```")

	# status
	@commands.hybrid_command(name="status", help="update bot's status")
	@app_commands.describe(activity_type="options: playing, listening, watching, competing, streaming", activity="name of activity")
	@commands.has_permissions(administrator=True)
	async def status(self, ctx, activity_type: str = None, *, activity: str = None):

		# ensure activity_type is valid
		activity_type_map = {
			"playing": discord.ActivityType.playing,
			"listening": discord.ActivityType.listening,
			"watching": discord.ActivityType.watching,
			"competing": discord.ActivityType.competing,
			"streaming": discord.ActivityType.streaming
		}
		
		try:
			config = json_load("config")
			main_config = config.setdefault("main", {})

			if activity_type is None or not activity_type.strip():
				activity_type = main_config.setdefault("activity_type", "playing")

			activity_type = activity_type.lower()

			if activity_type:
				if activity_type.lower() not in activity_type_map:
					await ctx.send("invalid option, use: `playing`, `listening`, `watching`, `competing`, `streaming`")
					return
				config.setdefault("main", {})["activity_type"] = activity_type.lower()
			
			if activity:
				main_config["activity"] = activity
			
			json_save("config", config)
			await update_status(self.bot)
			await ctx.send("status updated\n-# deleting..", delete_after=3)

		except FileNotFoundError:
			await ctx.send("config file not found")
		
		except json.JSONDecodeError:
			await ctx.send("error reading the json file")

	# say cmd
	@commands.command(name="say", help="make bot send a message")
	@commands.has_permissions(administrator=True)
	@commands.bot_has_permissions(manage_messages=True)
	async def say(self, ctx:Context, *, message: str = None) -> None:
		words = message.split() if message is not None else ['x', 'x', 'x']
		files = [await att.to_file() for att in ctx.message.attachments]

		if not message and not files:
			await ctx.send(
				"> requires atleast a message or a attachment\n> -# deleting...",
				delete_after = 5
			)
			return None

		reply_to_msg = True
		if words[0] == "uc":
			data = json_load("config")
			unichar = data.setdefault("unichar", {})

			if not unichar:return await ctx.send("> no emojis available, please use `say ucsetup`")

			message = ' '.join(words[1:])

			if not message.strip(): return await ctx.send("type something in {} for magik")

			def replace_braces(match):
				content = match.group(1)
				return ''.join(unichar.get(char.lower(), char) for char in content)

			# apply the transformation
			message = re.sub(r"\{([^{}]+)\}", replace_braces, message)
		
		elif words[0] == 'ucsetup':
			reply_to_msg = False
			if len(words) < 2:
				return await ctx.send("> usage: `ucsetup a-z/0-9` while replying to message containing emoji list")
			
			mode = words[1].lower()
			
			if not ctx.message.reference:return await ctx.send("> plaese reply to a message containing emojis")

			replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
			emoji_str = replied.content
			emojis = re.findall(r'<a?:[^:]+:\d+>', emoji_str)

			if mode == 'a-z':
				if len(emojis) < 26:
					return await ctx.send("> atleast provide 26 emojis for a-z letters")
				chars = [chr(i) for i in range(ord('a'), ord('z') +1)]
			
			elif mode == '0-9':
				if len(emojis) < 10:
					return await ctx.send("> atleast provide 10 emojis for 0-9 nums")
				chars = [str(i) for i in range(10)]
			else:
				return await ctx.send("> invalid mode, use `a-z` or `0-9`, custom range and individual char addition will be added soon")

			# create mapping
			mapping = dict(zip(chars, emojis))

			# load json
			data = json_load("config")
			data.setdefault("unichar", {}).update(mapping)
			json_save("config", data)

			return await ctx.send(f"> added emojis for `{mode}`")

		elif words[0] in ('-in'):
			reply_to_msg = False

			if len(words) < 2:
				return await ctx.send("> usage: `,say -in #channel <message>`\n> -# deleting...", delete_after=5)

			# parse channel mention
			channel_mention = words[1]
			if not (channel_id := re.findall(r"<#(\d+)>", channel_mention)):
				return await ctx.send("> please mention a valid channel\n> -# deleting...", delete_after=5)
			channel_id = int(channel_id[0])

			# resolve channel
			channel = ctx.guild.get_channel(channel_id)
			if not channel:
				return await ctx.send("> channel not found in this server\n> -# deleting...", delete_after=5)

			# message text = everything after channel mention
			message = " ".join(words[2:])
			if not message.strip():
				return await ctx.send("> please provide a message after the channel mention\n> -# deleting...", delete_after=5)

			# send in target channel
			await channel.send(
				content=message,
				files=files
			)
			try:
				await ctx.message.delete()
			except discord.Forbidden:
				pass
			return

		await ctx.send(
			content = message,
			files = files,
			reference=ctx.message.reference if reply_to_msg else None
		)
		try:
			await ctx.message.delete()
		except discord.Forbidden:
			pass

	# restart
	@commands.command(name="re", help="restart the bot")
	@commands.is_owner()
	async def xre(self, ctx):
		result = subprocess.run(
			['gitpull.bat'],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=True,
			text=True
		)
		output = result.stdout or result.stderr
		await reload_all_cogs(self.bot)
		await ctx.send(f">>> ```py\n{output[:1900]}\n```")
		print(output[:1900])
	
	# py
	@commands.command(name="py", help="execute python code")
	async def py(self, ctx, *, code: str = None):
		if not checkadmin(ctx):return await ctx.send(">>> yo aah ain't sem's admin for ts :wilted_rose:")

		if not code:
			if ctx.message.reference:
				replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
				code = replied.content
			else:
				return await ctx.send("> provide code or reply with empty msg to a message containing code")

		code = re.sub(r"^```(?:py)?\n([\s\S]*?)\n?```$", r"\1", code.strip())
		str_io = io.StringIO()

		with contextlib.redirect_stdout(str_io):
			exec(code, {})
		output = str_io.getvalue()
		await ctx.send(f">>> {output or 'no output'}")

	# sendembed cmd
	@commands.hybrid_command(name="sendembed", help="make bot send custom embed")
	@app_commands.describe(
		title="title of the embed",
		description="description of the embed",
		fields="dynamic fields as 'name & value' pairs separated by | (pipes)",
		footer="optional footer text",
		color="hex color (example #f1e3e2)"
	)
	@commands.has_permissions(administrator=True)
	async def sendembed(
		self,
		ctx: Context,
		title: str = None,
		description: str = None,
		fields: str = None,
		footer: str = None,
		color: str = "#f1e3e2"
	):
		# Convert hex color string to int
		try:
			embed_color = int(color.strip("#"), 16)
		except ValueError:
			await ctx.reply("invalid color format, use hex like #f1e3w2", ephemeral=True)
			return

		embed = discord.Embed(
			title=title or None,
			description=description or None,
			color=embed_color
		)

		if fields:
			for field in fields.split("|"):
				if "&"in field:
					name, value = field.split("&", 1)
					embed.add_field(name=name.strip(), value=value.strip(), inline=False)

		if footer:
			embed.set_footer(text=f"{footer}")

		await ctx.send(embed=embed)

async def setup(bot):
	await bot.add_cog(admin(bot))