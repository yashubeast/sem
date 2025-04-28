import discord, json
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands

json_file_path = "assets/servers.json"

class server(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
		# self.bot.db = await aiosqlite.connect("assets/sembase.db")
		# async with self.bot.db.cursor() as cursor:
			# await cursor.execute("CREATE TABLE IF NOT EXISTS catalog (name TEXT, msg_id INT, guild INT, channel INT)")

	# server (group)
	@commands.hybrid_group(help="tools for server listing")
	@commands.has_permissions(administrator=True)
	async def server(self, ctx):
		if ctx.invoked_subcommand is None:
			return await ctx.send("remind yasu to add something here.")

	# server add
	@server.command(name="add", aliases=["a"], help="Add a new server message")
	@app_commands.describe(name="Server name", message="Full message to store")
	async def add(self, ctx: Context, name: str, *, message: str):
		try:
			with open(json_file_path, "r", encoding="utf-8") as f:
				data = json.load(f)

			servers_list = data.get("servers_list", [])

			server_name = name.lower()

			if not server_name.strip():
				return await ctx.send("Server name cannot be empty.")

			servers_list.append({server_name: message})

			# Save back to JSON
			data["servers_list"] = servers_list
			with open(json_file_path, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=4)

			await ctx.send(f"Server `{server_name}` added successfully!")

		except Exception as e:
			await ctx.send(f"Error: {e}")

	# server delete
	@server.command(name="delete", aliases=["d", "del"], help="Delete a server message")
	@app_commands.describe(server="Name of the server to delete")
	async def delete(self, ctx, *,server: str):
		try:
			with open (json_file_path, "r") as f:
				data = json.load(f)

			servers_list = data.get("servers_list", [])

			if not any(server.lower() == key.lower() for entry in servers_list for key in entry):
				await ctx.send(f"Server `{server}` doesn't exist.")
				return
			
			for i, entry in enumerate(servers_list):
				if server.lower() in (key.lower() for key in entry):
					del servers_list[i]
					break

			with open (json_file_path, "w") as f:
				json.dump(data, f, indent=4)
			
			await ctx.send(f"Server `{server}` deleted.")

		except FileNotFoundError:
			await ctx.send("Server data fiel not found.")
		except json.JSONDecodeError:
			await ctx.send("Error reading the server data file.")
		except Exception as e:
			return await ctx.send(f"Error: {e}")

	# server list
	@server.command(name="list", alises=["l"], help="List all servers")
	async def list(self, ctx: Context):
		with open(json_file_path, "r") as f:
			data = json.load(f)

		servers_list = data.get("servers_list", [])

		if not servers_list:
			return await ctx.send("No servers in list")

		servers = "\n".join(f"- {list(server_name.keys())[0]}" for server_name in servers_list if server_name)
		await ctx.send(f"**Servers:**\n{servers}")

	# server show
	@server.command(name="show", aliases=["s"], help="Previews a server message")
	@app_commands.describe(server="Name of the server to send")
	async def show(self, ctx, *,server: str):
		try:
			with open (json_file_path, "r") as f:
				data = json.load(f)

			servers_list = data.get("servers_list", [])
			server_message = next((list(entry.values())[0] for entry in servers_list if server.lower() in (key.lower() for key in entry)))

			if not server_message:
				await ctx.send(f"Server `{server}` doesn't exist.")
				return
			
			await ctx.send(server_message)

		except FileNotFoundError:
			await ctx.send("Server data fiel not found.")
		except json.JSONDecodeError:
			await ctx.send("Error reading the server data file.")
		except Exception as e:
			return await ctx.send(f"Error: {e}")

	# server nuke
	@server.command(name="nuke", help="nukes data")
	async def nuke(self, ctx, target: str):
		try:
			target = target.lower()

			if target not in ["servers", "messages", "msgs"]:
				await ctx.send("invalid target")
				return

			# load json
			with open(json_file_path, "r", encoding="utf-8") as f:
				data = json.load(f)
			
			if target == "servers":
				data["servers_list"] = []
			elif target in ["messages", "msgs"]:
				data ["messages_list"] = []

			# update json
			with open(json_file_path, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=4)
			
			await ctx.send(f"nuked {target}")
		
		except Exception as e:
			await ctx.send(f"error: {e}")

	# server initiate, send all the server messages
	@server.command(name="initiate", aliases=["i"], help="Initiate all server messages")
	async def initiate(self, ctx: Context):
		# load json
		with open(json_file_path, "r", encoding="utf-8") as f:
			data = json.load(f)

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

			# look into this, probably not working as intended
			except discord.NotFound:
				# message doesn't exist, delete broken msg id
				del messages_list[idx]

				# update json
				data["messages_list"] = messages_list
				with open(json_file_path, "w", encoding="utf-8") as f:
					json.dump(data, f, indent=4)
				
				continue

			# error handling
			except Exception as e:
				await ctx.send(f"Error handling server `{server_name}`: {e}")
			
			idx += 1
			
		# update json
		data["messages_list"] = messages_list
		with open(json_file_path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=4)
		
		# if edited == 0 and added == 0:
		# 	await ctx.send("No changes made.\n-# auto deleting...", delete_after=7)
		# else:
		# 	await ctx.send(f"{added} servers added\n{edited} servers edited\n-# auto deleting...", delete_after=7)

	# server move (group)
	@server.group(help="repositioning commands for servers")
	async def move(self, ctx):
		if ctx.invoked_subcommand is None:
			return await ctx.send("use sub-commands: up, down, above, below, to")

	# server move up
	@move.command(name="up", alises=["u"], help="Move server's position up by X amount")
	async def up(self, ctx, name : str, amount: int):

		# load json
		with open (json_file_path, "r") as f:
			data = json.load(f)
		servers_list = data.get("servers_list", [])

		# find the index
		index = next((i for i, server in enumerate(servers_list) if name in server), None)

		if index is None:
			await ctx.send(f"Server {name} doesn't exist")
			return

		# calculate new position
		new_index = max(index - amount, 0)

		# move server
		server = servers_list.pop(index)
		servers_list.insert(new_index, server)

		# update json
		data["servers_list"] = servers_list
		with open(json_file_path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=4)

		await ctx.send(f"Server {name} moved up by {amount}")

	# server move down
	@move.command(name="down", aliases=["d"], help="Move a server's position down by X amount")
	async def down(self, ctx, name: str, amount: int):
		# load json
		with open(json_file_path, "r", encoding="utf-8") as f:
			data = json.load(f)

		servers_list = data.get("servers_list", [])

		# find the index
		index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)

		if index is None:
			await ctx.send(f"Server with key {name} doesn't exist")
			return

		# calculate new position
		new_index = min(index + amount, len(servers_list) - 1)

		# move server
		server = servers_list.pop(index)
		servers_list.insert(new_index, server)

		# update json
		data["servers_list"] = servers_list
		with open(json_file_path, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=4)

		await ctx.send(f"Server {name} moved down by {amount}")

	# server move to
	@move.command(name="to", aliases=["t"], help="Move a server to Xth position")
	async def to(self, ctx, name: str, index: int):
		try:
			# load json
			with open(json_file_path, "r", encoding="utf-8") as f:
				data = json.load(f)

			servers_list = data.get("servers_list", [])

			# find the index
			current_index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)

			if current_index is None:
				await ctx.send(f"Server {name} doesn't exist")
				return

			# ensuring target index is within bounds
			target_index = max(0, min(index -1, len(servers_list) -1))

			# move server
			server = servers_list.pop(current_index)
			servers_list.insert(target_index, server)

			# update json
			data["servers_list"] = servers_list
			with open(json_file_path, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=4)

			await ctx.send(f"Server {name} moved to position {index}")
		
		except Exception as e:
			await ctx.send(f"Error: {e}")

	# server move above
	@move.command(name="above", aliases=["a"], help="Move a server above another server")
	async def above(self, ctx, name: str, above_name: str):
		try:
			# load json
			with open(json_file_path, "r", encoding="utf-8") as f:
				data = json.load(f)

			servers_list = data.get("servers_list", [])

			# find indices
			moving_index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)
			target_index = next((i for i, server in enumerate(servers_list) if above_name.lower() in (key.lower() for key in server)), None)

			if moving_index is None:
				await ctx.send(f"Server {name} doesn't exist")
				return

			if target_index is None:
				await ctx.send(f"Server {above_name} doesn't exist")
				return

			# remove moving server
			server = servers_list.pop(moving_index)

			# adjust target_index if necessary
			if moving_index < target_index:
				target_index -= 1

			# insert moving server above target
			servers_list.insert(target_index, server)

			# save
			data["servers_list"] = servers_list
			with open(json_file_path, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=4)

			await ctx.send(f"Moved {name} above {above_name}")
			
		except Exception as e:
			await ctx.send(f"Error: {e}")

	# server move below
	@move.command(name="below", aliases=["b"], help="Move a server below another server")
	async def below(self, ctx, name: str, below_name: str):
		try:
			# load json
			with open(json_file_path, "r", encoding="utf-8") as f:
				data = json.load(f)

			servers_list = data.get("servers_list", [])

			# find indices
			moving_index = next((i for i, server in enumerate(servers_list) if name.lower() in (key.lower() for key in server)), None)
			target_index = next((i for i, server in enumerate(servers_list) if below_name.lower() in (key.lower() for key in server)), None)

			if moving_index is None:
				await ctx.send(f"Server {name} doesn't exist")
				return

			if target_index is None:
				await ctx.send(f"Server {below_name} doesn't exist")
				return

			# remove moving server
			server = servers_list.pop(moving_index)

			# adjust target_index if necessary
			if moving_index < target_index:
				target_index -= 1

			# insert moving server below target
			servers_list.insert(target_index + 1, server)

			# update json
			data["servers_list"] = servers_list
			with open(json_file_path, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=4)

			await ctx.send(f"Moved {name} below {below_name}")
			
		except Exception as e:
			await ctx.send(f"Error: {e}")

	# server import (group)
	@server.group(name="import", help="import messages as server")
	async def ximport(self, ctx):
		if ctx.invoked_subcommand is None:
			return await ctx.send("use import sub commands as, bulk")

	# server import as
	@ximport.command(name="as", help="import replied message as a server message")
	async def xas(self, ctx, *, name: str, message_id: str = None):
		try:
			if ctx.interaction is None:
				if ctx.message.reference:
					replied_message_id = ctx.message.reference.message_id
					replied_message = await ctx.channel.fetch_message(replied_message_id)
					server_content = replied_message.content

					# load json
					with open(json_file_path, "r", encoding="utf-8") as f:
						data = json.load(f)
					
					servers_list = data.get("servers_list", [])
					servers_list.append({name: server_content})

					# update json
					data["servers_list"] = servers_list
					with open(json_file_path, "w", encoding="utf-8") as f:
						json.dump(data, f, indent=4)
					
					await ctx.send(f"Server {name} imported")
				else:
					await ctx.send("You need to reply to a message")
			else:
				if message_id:
					app_replied_message_id = int(message_id)
					app_replied_message = await ctx.channel.fetch_message(app_replied_message_id)
					app_server_content = app_replied_message.content

					# load json
					with open(json_file_path, "r", encoding="utf-8") as f:
						data = json.load(f)
					
					servers_list = data.get("servers_list", [])
					servers_list.append({name: app_server_content})

					# update json
					data["servers_list"] = servers_list
					with open(json_file_path, "w", encoding="utf-8") as f:
						json.dump(data, f, indent=4)				
					
					await ctx.send(f"Server {name} imported")
				else:
					await ctx.send("please provide a message id for importing")

		except Exception as e:
			await ctx.send(f"Error: {str(e)}")

	# server import bulk
	@ximport.command(name="bulk", help="Bulk import server messages from message IDs")
	async def bulk(self, ctx, from_id: str, to_id: str, user: discord.User = None, exclude: str = None):
		try:
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
				await ctx.send("No messages collected.")
				return

			# load json
			with open(json_file_path, "r", encoding="utf-8") as f:
				data = json.load(f)

			servers_list = data.get("servers_list", [])

			# add collected message to list
			for msg in reversed(collected_messages):
				servers_list.append({f"{msg.id}": msg.content})

			# update json
			data["servers_list"] = servers_list
			with open(json_file_path, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=4)

			await ctx.send(f"Successfully imported {len(collected_messages)} messages.")

		except Exception as e:
			await ctx.send(f"Error: {str(e)}")

	# visible cmd
	@commands.hybrid_command(name="server_visibility", aliases=["sv"], help="toggle visibility of server", with_app_command=True)
	@commands.has_permissions(administrator=True)
	async def server_visibility(self, ctx, name: str):
		try:
			with open(json_file_path, "r") as f:
				data = json.load(f)
			
			servers = data.get("servers", {})
			visible_servers = data.get("visible_servers", {})

			# find the input name in servers list
			server = servers.get(name.lower())

			# server doesn't exist in servers
			if server is None:
				await ctx.send(f"{name} server not found.")
				return

			# if server is visible already
			if name in visible_servers:
				# server is already visible
				server_data = visible_servers[name]
				message_id = server_data.get("message_id")
				channel_id = server_data.get("channel_id")

				if message_id and channel_id:
					try:
						channel = await self.bot.fetch_channel(int(channel_id))
						message = await channel.fetch_message(int(message_id))
						await message.delete()

					except Exception as e:
						await ctx.send(f"Failed to delete message (possibly inexistant): {e}")

				del visible_servers[name]
				await ctx.send(f"{name} server hidden.")

			else:
				# server is NOT visible
				visible_servers[name] = {}
				await ctx.send(f"{name} server displayed.")

			data["visible_servers"] = visible_servers
			with open(json_file_path, "w", encoding="utf-8") as f:
				json.dump(data, f, indent=4)

		except Exception as e:
			await ctx.send(f"Error: {e}")

async def setup(bot):
	await bot.add_cog(server(bot))