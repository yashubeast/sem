import discord, aiohttp, time
from discord.ext import commands
from utils.values import checkserver

class semity(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.user_last_message_time = {}
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	@commands.Cog.listener()
	async def on_message(self, message):
		
		if not checkserver(message): return

		if message.author.bot:return

		user_id = message.author.id
		server_id = message.guild.id if message.guild else None
		msg_len = len(message.content)

		# time since last message
		current_time = time.time()

		if user_id in self.user_last_message_time:
			time_since_last = current_time - self.user_last_message_time[user_id]
		else:
			time_since_last = None # first message from user

		self.user_last_message_time[user_id] = current_time

		if time_since_last is None: time_since_last = 0
		
		# message formula
		async with aiohttp.ClientSession() as session:
			async with session.post(
				"http://localhost:8000/discord/equity/message/formula",
				json={
					"user_id": user_id,
					"server_id": server_id,
					"message_length": msg_len,
					"message_time_gap": time_since_last
				}
			) as resp:
				if resp.status == 200:
					data = await resp.json()
					print(f'{message.author}: {message.guild.name} -> len: {data["message_length"]}, time: {data["message_time_gap"]}, msgs: {data["message_count"]} = {data["total"]}')
				else:
					print(f"api error: {resp.status}")

		# message count
		async with aiohttp.ClientSession() as session:
			async with session.post(
				"http://localhost:8000/discord/equity/message/add",
				json={
					"user_id": user_id,
					"server_id": server_id
				}
			) as resp:
				if resp.status == 200:
					data = await resp.json()
					print(f"{message.author} -> message count: {data['message_count']}")
				else:
					print(f"api error: {resp.status}")
	
	@commands.Cog.listener()
	async def on_message_delete(self, message):

		if message.author.bot or not message.guild:return

		user_id = message.author.id
		server_id = message.guild.id

		async with aiohttp.ClientSession() as session:
			url = "http://localhost:8000/discord/equity/message/remove"
			json = {
				"user_id": user_id,
				"server_id": server_id
			}

			async with session.post(url, json=json) as resp:
				if resp.status == 404:
					print(f"no entry for user {message.author}")
				elif resp.status == 400:
					print(f"count 0 for user {message.author}")
				elif resp.status == 200:
					data = await resp.json()
					print(f"{message.author} -> message count: {data['message_count']}")
				else:
					print(f"error updating message count for {message.author}")
	
	# semity group
	@commands.group(name="semity")
	async def semity(self, ctx):
		pass

	@semity.command(name="msgcount", description="get message count for a user, total/specified server")
	async def msgcount(self, ctx, user: discord.User = None, server: int = None):
		user_id = (user or ctx.author).id
		server_name = await self.bot.fetch_guild(server) if server else None

		async with aiohttp.ClientSession() as session:
			url = f"http://localhost:8000/discord/equity/message/{user_id}" + (f"?server_id={server}" if server else "")
			async with session.get(url) as resp:
				if resp.status == 404:
					msg = ("> no entry for user")
					if server:
						msg += f" in specified server"
					await ctx.send(msg)
					return
				
				data = await resp.json()
				msg = f"> {user.mention if user else ctx.author.mention} has sent {data['message_count']} messages"
				if server_name:
					msg += f" in {server_name}"
				await ctx.send(msg)
	
	# semity balance
	@semity.command(name="balance", description="get balance for a user")
	async def balance(self, ctx, user: discord.User = None):
		user = user or ctx.author
		user_id = user.id

		async with aiohttp.ClientSession() as session:
			url = f"http://localhost:8000/discord/equity/coin/balance/{user_id}"
			async with session.get(url) as resp:
				if resp.status == 404:
					await ctx.send(f"> no entry for user {user.mention}")
					return
				
				data = await resp.json()
				await ctx.send(f"> {user.mention} has {data['coins']} coins")

async def setup(bot):
	await bot.add_cog(semity(bot))