import discord, json, time
from discord.ext import commands
# from discord.ext.commands import Context
from discord import app_commands

json_file_path = "assets/servers.json"
active_channels = set()
working_channels = set()

def json_load():
	with open(json_file_path, "r", encoding="utf-8") as f:
		return json.load(f)

def json_save(data):
	with open(json_file_path, "w", encoding="utf-8") as f:
		json.dump(data, f, indent=4)

class sticky(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.sticky_channel_cache = []
		self.last_msg_time = {}

	def cache_update(self):
		data = json_load()
		self.sticky_channel_cache = data.setdefault("sticky", {}).setdefault("sticky_channels", [])
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
		self.cache_update()

	# resend sticky when someone sends a message below it
	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		try:
			channel = message.channel
			channel_id = str(message.channel.id)

			# return if channel is not a sticky_channel
			if channel_id not in self.sticky_channel_cache:return

			# return if channel is locked, else lock the channel
			if channel_id in active_channels:return
			if channel_id in working_channels:return
			active_channels.add(channel_id)

			# return if last resend was done recently
			now = time.time()
			last_time = self.last_msg_time.get(channel_id, 0)

			if now - last_time <3:
				return
			
			self.last_msg_time[channel_id] = now

			# channel is sticky

			# load json
			data = json_load()
			sticky = data.get("sticky", {}).get(channel_id)

			# get latest message instead of new
			latest_msg = [msg async for msg in channel.history(limit=1)][0]

			# return if new message is a sticky message
			if not sticky:return
			if sticky["last_id"] == latest_msg.id:return

			# new message detected, actual command runs now

			# delete old sticky
			try:
				msg_to_delete = await message.channel.fetch_message(sticky["last_id"])
				await msg_to_delete.delete()
			# continue if it doesn't exist
			except (discord.NotFound, discord.HTTPException):
				pass

			# send new sticky
			new_msg = await message.channel.send(f"{sticky['content']}")

			# save json
			data["sticky"][channel_id]["last_id"] = new_msg.id
			json_save(data)
	
		except Exception as e:
			await message.channel.send(f"error: {e}")

		finally:
			active_channels.remove(channel_id)

	# sticky create
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	async def sticky(self, ctx, *, content: str):

		channel_id = str(ctx.channel.id)

		working_channels.add(channel_id)

		data = json_load()

		# add channel to sticky_channels dictionary list, if it doesn't already exist
		if channel_id not in data.setdefault("sticky", {}).setdefault("sticky_channels", []):
			data.setdefault("sticky", {}).setdefault("sticky_channels", []).append(channel_id)
			self.sticky_channel_cache.append(channel_id)

		msg = await ctx.channel.send(f"{content}")
		data.setdefault("sticky", {})[channel_id] = {
			"content": content,
			"last_id": msg.id
		}
		json_save(data)

		working_channels.remove(channel_id)

		# await ctx.send("sticky message set -# deleting...", delete_after=5)

	# sticky delete
	@commands.command()
	@commands.has_permissions(manage_messages=True)
	async def unsticky(self, ctx):
		channel_id = str(ctx.channel.id)
		data = json_load()

		if channel_id not in data:
			await ctx.send("no sticky message set for this channel")
			return

		# attempt to delete sticky message
		try:
			last_msg = await ctx.channel.fetch_message(data[channel_id]["last_id"])
			await last_msg.delete()
		except (discord.NotFound, discord.HTTPException):
			pass

		del data[channel_id]
		json_save(data)

		await ctx.send("sticky message removed", delete_after=5)

	# if sticky message is deleted
	# @commands.Cog.listener()
	# async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
	# 	channel_id = str(payload.channel_id)
		
	# 	# load json
	# 	data = json_load()

	# 	if channel_id not in data:
	# 		return
	# 	if payload.message_id != data[channel_id].get("last_id"):
	# 		return

	# 	channel = self.bot.get_channel(payload.channel_id)
	# 	if channel is None:
	# 		return

	# 	# repost the sticky message
	# 	try:
	# 		new_msg = await channel.send(f"__**Stickied Message:**__\n\n{data[channel_id]['content']}")
	# 		data[channel_id]["last_id"] = new_msg.id

	# 		# save json
	# 		json_save(data)

	# 	except Exception as e:
	# 		print(f"failed to resend sticky message: {e}")

async def setup(bot):
	await bot.add_cog(sticky(bot))