import discord, json, time, os
from discord.ext import commands
from discord import app_commands
from utils.json_handler import json_load, json_save

json_file_path = "assets/sticky.json"
active_channels = set()
working_channels = set()

class sticky(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.last_msg_time = {}
	
	@commands.Cog.listener()
	async def on_ready(self):
		await self.bot.wait_until_ready()
		print(f"{__name__} is online!")

	# resend sticky when someone sends a message below it
	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		try:
			channel = message.channel
			channel_id = str(channel.id)

			# return if channel is not a sticky_channel
			if channel_id not in json_load("sticky").setdefault("sticky", {}).setdefault("sticky_channels", []):return

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
			data = json_load("sticky")
			sticky = data.setdefault("sticky", {}).get(channel_id)

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
			json_save("sticky", data)
	
		except Exception as e:
			raise Exception(f"{e}")

		finally:
			active_channels.discard(channel_id)

	# sticky (group)
	@commands.hybrid_group(help="sticky message commands")
	@commands.has_permissions(manage_messages=True)
	async def sticky(eslf, ctx):
		if ctx.invoked_subcommand is None:
			pass

	# sticky create/edit
	@sticky.command(name="create", aliases=["c"], help="new sticky message, or overwrite existing one")
	@app_commands.describe(content="content of sticky message")
	async def create(self, ctx, *, content: str):
		try:
			channel_id = str(ctx.channel.id)

			working_channels.add(channel_id)

			data = json_load("sticky")

			old_sticky = data.setdefault("sticky", {}).get(channel_id)
			if old_sticky:
				try:
					last_msg = await ctx.channel.fetch_message(old_sticky["last_id"])
					await last_msg.delete()
				except (discord.NotFound, discord.HTTPException):
					pass

			# add channel to sticky_channels dictionary list, if it doesn't already exist
			sticky_channels = data.setdefault("sticky", {}).setdefault("sticky_channels", [])
			if channel_id not in sticky_channels:
				sticky_channels.append(channel_id)

			msg = await ctx.channel.send(f"{content}")
			data.setdefault("sticky", {})[channel_id] = {
				"content": content,
				"last_id": msg.id
			}
			json_save("sticky", data)

		finally:
			working_channels.discard(channel_id)

	# sticky remove
	@sticky.command(name="remove", aliases=["r", "d", "del"], help="remove sticky message")
	async def remove(self, ctx, channel: discord.TextChannel = None):
		try:
			target_channel = channel or ctx.channel
			channel_id = str(target_channel.id)

			data = json_load("sticky")
			if channel_id not in data.setdefault("sticky", {}).setdefault("sticky_channels", []):return await ctx.send(f">>> no sticky message in {target_channel.mention}\n-# deleting..", delete_after=3)

			working_channels.add(channel_id)

			# attempt to delete sticky message
			try:
				last_msg = await target_channel.fetch_message(data["sticky"][channel_id]["last_id"])
				await last_msg.delete()
			except (discord.NotFound, discord.HTTPException):
				pass

			sticky_channels = data.setdefault("sticky", {}).setdefault("sticky_channels", [])
			if channel_id in sticky_channels:
				sticky_channels.remove(channel_id)

			if channel_id in data["sticky"]:
				del data["sticky"][channel_id]

			json_save("sticky", data)

			await ctx.send(f"sticky message removed{f' from {target_channel.mention}' if channel else ''}\n-# deleting...", delete_after=5)

		finally:
			working_channels.discard(channel_id)

	# sticky list
	@sticky.command(name="list", aliases=["l"], help="list all channels with active sticky messages")
	async def list(self, ctx):
		data = json_load("sticky")
		sticky_data = data.setdefault("sticky", {})
		sticky_channels = sticky_data.setdefault("sticky_channels", [])

		if not sticky_channels:
			return await ctx.send(">>> no active sticky messages\n-# deleting..", delete_after=3)

		lines = []
		for channel_id in sticky_channels:
			channel = self.bot.get_channel(int(channel_id))
			if channel:
				lines.append(f"- <#{channel.id}>")
			else:
				lines.append(f"- unknown channel (id: `{channel_id}`)")

		message = ">>> sticky messages active in:\n" + "\n".join(lines)
		await ctx.send(message)

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