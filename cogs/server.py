import discord, json
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

json_file_path = "assets/servers.json"

def json_load():
	with open(json_file_path, "r", encoding="utf-8") as f:
		return json.load(f)

def json_save(data):
	with open(json_file_path, "w", encoding="utf-8") as f:
		json.dump(data, f, indent=4)

class server(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	# server (group)
	@commands.hybrid_group(help="tools for server listing", aliases=["s"])
	@commands.has_permissions(administrator=True)
	async def server(self, ctx):
		if ctx.invoked_subcommand is None:
			pass

	# server add
	@server.command(name="add", aliases=["a"], help="add/edit a server")
	@app_commands.describe(name="server name", message="full message to store")
	async def add(self, ctx: Context, name: str, *, message: str):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		server_name = name.lower().strip

		if not server_name:
			return await ctx.send("server name cannot be empty")

		# check if server already exists
		updated = False
		for server in servers_list:
			if server_name == server:
				server[server_name] = message
				update = True
				break

		if not updated:
			servers_list.append({server_name: message})

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"server `{server_name}` {'updated' if updated else 'added'}")

	# server delete
	@server.command(name="delete", aliases=["d", "del"], help="delete a server")
	@app_commands.describe(server="name of the server to delete")
	async def delete(self, ctx, *,server: str):
		try:
			# load json
			data = json_load()

			servers_list = data.get("servers_list", [])

			if not any(server.lower() == key.lower() for entry in servers_list for key in entry):
				await ctx.send(f"server `{server}` doesn't exist ")
				return
			
			for i, entry in enumerate(servers_list):
				if server.lower() in (key.lower() for key in entry):
					del servers_list[i]
					break

			# save json
			json_save(data)
			
			await ctx.send(f"server `{server}` deleted")

		except FileNotFoundError:
			await ctx.send("server data file not found")
		except json.JSONDecodeError:
			await ctx.send("error reading the server data file")

	# server list
	@server.command(name="list", alises=["l"], help="list all servers")
	async def list(self, ctx: Context):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		if not servers_list:
			return await ctx.send("no servers in list")

		servers = "\n".join(f"- {list(server_name.keys())[0]}" for server_name in servers_list if server_name)
		await ctx.send(f"**servers:**\n{servers}")

	# server show
	@server.command(name="show", aliases=["s"], help="previews a server message")
	@app_commands.describe(server="name of the server to show")
	async def show(self, ctx, *,server: str):
		try:
			data = json_load()

			servers_list = data.get("servers_list", [])
			server_message = next((list(entry.values())[0] for entry in servers_list if server.lower() in (key.lower() for key in entry)))

			if not server_message:
				await ctx.send(f"server `{server}` doesn't exist")
				return
			
			await ctx.send(server_message)

		except FileNotFoundError:
			await ctx.send("server data fiel not found.")
		except json.JSONDecodeError:
			await ctx.send("error reading the server data file.")

	# server nuke
	@server.command(name="nuke", help="nukes data")
	@app_commands.describe(target="options: servers, messages(msgs)")
	async def nuke(self, ctx, target: str):
		target = target.lower()

		if target not in ["servers", "messages", "msgs"]:
			await ctx.send("invalid target")
			return

		# load json
		data = json_load()
		
		if target == "servers":
			data["servers_list"] = []
		elif target in ["messages", "msgs"]:
			data ["messages_list"] = []

		# save json
		json_save(data)

		await ctx.send(f"nuked `{target}`")

	# server initiate, send all the server messages
	@server.command(name="initiate", aliases=["i"], help="initiate all server")
	async def initiate(self, ctx: Context):
		# load json
		data = json_load()

		# load dicts
		servers_list = data.get("servers_list", [])
		messages_list = data.get("messages_list", [])

		# load keys from dicts
		server_names = [list(entry.keys())[0] for entry in servers_list]
		messages_ids = messages_list
		
		edited = 0
		added = 0
		idx = 0

		while idx < len(server_names):
			server_name = server_names[idx]

			# content of current server name
			server_content = next((list(entry.values())[0] for entry in servers_list if server_name.lower() == list(entry.keys())[0].lower()), None)

			# if theres a message id at current index
			try:
				message_id = messages_ids[idx]
				channel = ctx.channel
				message = await channel.fetch_message(int(message_id))

				# comparing content of existing msg vs stored msg
				if message.content.strip() != server_content.strip():
					# content mismatch, fix mismatch (overwrite)
					await message.edit(content=server_content)
					edited += 1

			# no msg at current index, create a new one
			except IndexError:
				new_message = await ctx.send(server_content)
				added += 1
				# save id to messages_list
				messages_list.append(str(new_message.id))

			# initiated message deleted (i forgot how this logic works in its entirety so i have nothing to explain here)
			except discord.NotFound:
				# message doesn't exist, delete broken msg id
				del messages_list[idx]

				# save json
				data["messages_list"] = messages_list
				json_save(data)
				
				continue
			
			idx += 1
			
		# save json
		data["messages_list"] = messages_list
		json_save(data)
		
		# if edited == 0 and added == 0:
		# 	await ctx.send("No changes made.\n-# auto deleting...", delete_after=7)
		# else:
		# 	await ctx.send(f"{added} servers added\n{edited} servers edited\n-# auto deleting...", delete_after=7)

	# server move (group)
	@server.group(help="repositioning commands for servers")
	async def move(self, ctx):
		if ctx.invoked_subcommand is None:
			pass

	# server move up
	@move.command(name="up", alises=["u"], help="move up by X amount")
	@app_commands.describe(name="server to move", amount="amount to move by")
	async def up(self, ctx, name : str, amount: int):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		# find the index
		index = next((i for i, server in enumerate(servers_list) if name in server), None)

		if index is None:
			await ctx.send(f"server `{name}` doesn't exist")
			return

		# calculate new position
		new_index = max(index - amount, 0)

		# move server
		server = servers_list.pop(index)
		servers_list.insert(new_index, server)

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"server `{name}` moved up by `{amount}`")

	# server move down
	@move.command(name="down", aliases=["d"], help="move down by X amount")
	@app_commands.describe(name="server to move", amount="amount to move by")
	async def down(self, ctx, name: str, amount: int):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		# find the index
		index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)

		if index is None:
			await ctx.send(f"server `{name}` doesn't exist")
			return

		# calculate new position
		new_index = min(index + amount, len(servers_list) - 1)

		# move server
		server = servers_list.pop(index)
		servers_list.insert(new_index, server)

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"server {name} moved down by `{amount}`")

	# server move to
	@move.command(name="to", aliases=["t"], help="move to Xth position")
	@app_commands.describe(name="server to move", index="position to move to")
	async def to(self, ctx, name: str, index: int):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		# find the index
		current_index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)

		if current_index is None:
			await ctx.send(f"server `{name}` doesn't exist")
			return

		# ensuring target index is within bounds
		target_index = max(0, min(index -1, len(servers_list) -1))

		# move server
		server = servers_list.pop(current_index)
		servers_list.insert(target_index, server)

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"server `{name}` moved to position `{index}`")

	# server move above
	@move.command(name="above", aliases=["a"], help="move above another server")
	@app_commands.describe(name="server to move", above_name="name of the server to move above")
	async def above(self, ctx, name: str, above_name: str):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		# find indices
		moving_index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)
		target_index = next((i for i, server in enumerate(servers_list) if above_name.lower() in (key.lower() for key in server)), None)

		if moving_index is None:
			await ctx.send(f"server `{name}` doesn't exist")
			return

		if target_index is None:
			await ctx.send(f"server `{above_name}` doesn't exist")
			return

		# remove moving server
		server = servers_list.pop(moving_index)

		# adjust target_index if necessary
		if moving_index < target_index:
			target_index -= 1

		# insert moving server above target
		servers_list.insert(target_index, server)

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"moved `{name}` above `{above_name}`")
			
	# server move below
	@move.command(name="below", aliases=["b"], help="move below another server")
	@app_commands.describe(name="server to move", below_name="name of the server to move below")
	async def below(self, ctx, name: str, below_name: str):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		# find indices
		moving_index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)
		target_index = next((i for i, server in enumerate(servers_list) if below_name.lower() in (key.lower() for key in server)), None)

		if moving_index is None:
			await ctx.send(f"server `{name}` doesn't exist")
			return

		if target_index is None:
			await ctx.send(f"server `{below_name}` doesn't exist")
			return

		# remove moving server
		server = servers_list.pop(moving_index)

		# adjust target_index if necessary
		if moving_index < target_index:
			target_index -= 1

		# insert moving server below target
		servers_list.insert(target_index + 1, server)

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"moved `{name}` below `{below_name}`")
			
	# server import (group)
	@server.group(name="import", help="import messages as server")
	async def ximport(self, ctx):
		if ctx.invoked_subcommand is None:
			return await ctx.send("use import subcommands: as, bulk")

	# server import as
	@ximport.command(name="as", help="import replied message as a server message")
	@app_commands.describe(name="server to move", message_id="id of message to import")
	async def xas(self, ctx, *, name: str, message_id: str = None):
		if ctx.interaction is None:
			if ctx.message.reference:
				replied_message_id = ctx.message.reference.message_id
				replied_message = await ctx.channel.fetch_message(replied_message_id)
				server_content = replied_message.content

				# load json
				data = json_load()
				
				servers_list = data.get("servers_list", [])
				servers_list.append({name: server_content})

				# save json
				data["servers_list"] = servers_list
				json_save(data)
				
				await ctx.send(f"server `{name}` imported")
			else:
				await ctx.send("you need to reply to a message")
		else:
			if message_id:
				app_replied_message_id = int(message_id)
				app_replied_message = await ctx.channel.fetch_message(app_replied_message_id)
				app_server_content = app_replied_message.content

				# load json
				data = json_load()
				
				servers_list = data.get("servers_list", [])
				servers_list.append({name: app_server_content})

				# save json
				data["servers_list"] = servers_list
				json_save(data)
				
				await ctx.send(f"server `{name}` imported")
			else:
				await ctx.send("please provide a message id for importing")

	# server import bulk
	@ximport.command(name="bulk", help="bulk import server messages using range")
	@app_commands.describe(from_id="bottom message_id of range", to_id="top message_id of range", user="specify user to look messages of", exclude="content to be excluded")
	async def bulk(self, ctx, from_id: str, to_id: str, user: discord.User = None, exclude: str = None):
		collected_messages = []
		found_from = False

		async for message in ctx.channel.history(limit=None, oldest_first=False):
			if user and message.author.id != user.id:
				continue

			if exclude and exclude in message.content:
				continue

			if not found_from:
				if message.id == int(from_id):
					found_from = True
					collected_messages.append(message)
			else:
				collected_messages.append(message)
				if message.id == int(to_id):
					break

		if not collected_messages:
			await ctx.send("no messages collected")
			return

		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		# add collected message to list
		for msg in reversed(collected_messages):
			servers_list.append({f"{msg.id}": msg.content})

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"successfully imported {len(collected_messages)} messages")

	# visible cmd
	# @commands.hybrid_command(name="server_visibility", aliases=["sv"], help="toggle visibility of server", with_app_command=True)
	# @commands.has_permissions(administrator=True)
	# async def server_visibility(self, ctx, name: str):
	# 	try:
	# 		with open(json_file_path, "r") as f:
	# 			data = json.load(f)
			
	# 		servers = data.get("servers", {})
	# 		visible_servers = data.get("visible_servers", {})

	# 		# find the input name in servers list
	# 		server = servers.get(name.lower())

	# 		# server doesn't exist in servers
	# 		if server is None:
	# 			await ctx.send(f"{name} server not found.")
	# 			return

	# 		# if server is visible already
	# 		if name in visible_servers:
	# 			# server is already visible
	# 			server_data = visible_servers[name]
	# 			message_id = server_data.get("message_id")
	# 			channel_id = server_data.get("channel_id")

	# 			if message_id and channel_id:
	# 				try:
	# 					channel = await self.bot.fetch_channel(int(channel_id))
	# 					message = await channel.fetch_message(int(message_id))
	# 					await message.delete()

	# 				except Exception as e:
	# 					await ctx.send(f"Failed to delete message (possibly inexistant): {e}")

	# 			del visible_servers[name]
	# 			await ctx.send(f"{name} server hidden.")

	# 		else:
	# 			# server is NOT visible
	# 			visible_servers[name] = {}
	# 			await ctx.send(f"{name} server displayed.")

	# 		data["visible_servers"] = visible_servers
	# 		with open(json_file_path, "w", encoding="utf-8") as f:
	# 			json.dump(data, f, indent=4)

	# 	except Exception as e:
	# 		await ctx.send(f"Error: {e}")

async def setup(bot):
	await bot.add_cog(server(bot))