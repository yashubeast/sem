import discord, aiohttp
from discord.ext import commands
from discord.ext.commands import Context
from utils.values import default_color


class test(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	@commands.Cog.listener()
	async def on_message(self, message):
		
		if message.author.bot:return

		user_id = message.author.id
		server_id = message.guild.id if message.guild else None

		async with aiohttp.ClientSession() as session:
			async with session.post(
				"http://localhost:8000/messages/add",
				json={
					"user_id": user_id,
					"server_id": server_id
				}
			) as resp:
				if resp.status == 200:
					data = await resp.json()
					await message.channel.send(f"message count updated: {data['message_count']}")
				else:
					print(f"api error: {resp.status}")
	
	@commands.Cog.listener()
	async def on_message_delete(self, message):

		if message.author.bot or not message.guild:return

		user_id = message.author.id
		server_id = message.guild.id

		async with aiohttp.ClientSession() as session:
			url = "http://localhost:8000/messages/remove"
			json = {
				"user_id": user_id,
				"server_id": server_id
			}

			async with session.post(url, json=json) as resp:
				if resp.status == 404:
					await message.channel.send(f"> no entry for user {message.author.mention}")
				elif resp.status == 400:
					await message.channel.send(f"> count 0 for user {message.author.mention}")
				elif resp.status == 200:
					data = await resp.json()
					await message.channel.send(f"> message count updated: {data['message_count']} for {message.author.mention}")
				else:
					await message.channel.send(f"> error updating message count for {message.author.mention}")
	
	@commands.command(name="msgcount")
	async def msgcount(self, ctx, user: discord.User = None, server: int = None):
		user_id = (user or ctx.author).id
		server_id = server or (ctx.guild.id if ctx.guild else None)

		async with aiohttp.ClientSession() as session:
			url = f"http://localhost:8000/messages/{user_id}?server_id={server_id}"
			async with session.get(url) as resp:
				if resp.status == 404:
					await ctx.send("> no entry for user")
					return
				
				data = await resp.json()
				await ctx.send(f"> {user.mention if user else ctx.author.mention} has sent {data['message_count']} messages in `{await self.bot.fetch_guild(server) if server else ctx.guild.name}`")

async def setup(bot):
	await bot.add_cog(test(bot))