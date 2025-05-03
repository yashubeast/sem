import discord, json, os, asyncio
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from typing import Tuple

json_file_path = "assets/server.json"
default_color = discord.Color.from_rgb(241, 227, 226)

def build_message_sequences(contents, separator, use_separators, include_edges):
	sequence = []
	for i, content in enumerate(contents):
		if i == 0 and use_separators and include_edges:
			sequence.append(("separator", separator))
		
		sequence.append(("content", content))
		
		if use_separators and (i < len(contents) -1 or (i == len(contents) -1 and include_edges)):
			sequence.append(("separator", separator))
	
	return sequence

def calc_index(servers_list, name):
	index = next((i for i, server in enumerate(servers_list) if name == list(server.keys())[0].lower()), None)
	return index

def ensure_json():
	os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
	if not os.path.isfile(json_file_path):
		with open(json_file_path, "w", encoding="utf-8") as f:
			json.dump({"servers_list": [], "messages_list": []}, f, indent=4)

def json_load():
	ensure_json()
	with open(json_file_path, "r", encoding="utf-8") as f:
		return json.load(f)

def json_save(data):
	ensure_json()
	with open(json_file_path, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=4)

class server(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	# server (group)
	@commands.hybrid_group(help="tools for server listing | previews server", aliases=["s"])
	@commands.has_permissions(administrator=True)
	async def server(self, ctx, *, name: str = None):
		subcommand = [cmd.name for cmd in ctx.command.commands]
		if not name:return await ctx.send(">>> provide server name to preview\n-# deleting..", delete_after=3)
		name = name.lower().strip()
		if name not in subcommand:
			data = json_load()

			servers_list = data.get("servers_list", [])
			server_message = next((list(entry.values())[0] for entry in servers_list if name in (key.lower() for key in entry)), None)

			if server_message is None:
				await ctx.send(f">>> server `{name}` doesn't exist\n-# deleting..", delete_after=3)
				await ctx.message.delete()
				return
			
			await ctx.send(server_message)
			await ctx.message.delete()

	# server add
	@server.command(name="add", aliases=["a"], help="add/edit a server")
	@app_commands.describe(name="server name", message="full message to store")
	async def add(self, ctx: Context, name: str, *, message: str):
		# load json
		data = json_load()

		servers_list = data.get("servers_list", [])

		server_name = name.lower().strip()

		if not server_name:
			return await ctx.send("server name cannot be empty")

		# check if server already exists
		updated = False
		for server in servers_list:
			if server_name == next(iter(server)):
				server[server_name] = message
				updated = True
				break

		if not updated:
			servers_list.append({server_name: message})

		# save json
		data["servers_list"] = servers_list
		json_save(data)

		await ctx.send(f"server `{server_name}` {'updated' if updated else 'added'}")

	# server remove
	@server.command(name="remove", aliases=["r", "rm", "d", "del"], help="remove a server")
	@app_commands.describe(server="name of the server to remove")
	async def remove(self, ctx, *,server: str):
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
			
			await ctx.send(f"server `{server}` removed")

		except FileNotFoundError:
			await ctx.send("server data file not found")
		except json.JSONDecodeError:
			await ctx.send("error reading the server data file")

	# server list
	@server.command(name="list", aliases=["l"], help="list all servers")
	async def list(self, ctx: Context):
		# load json
		data = json_load()
		servers_list = data.get("servers_list", [])

		if not servers_list:
			return await ctx.send("no servers in list")

		total = len(servers_list)
		midpoint = total // 2 + total % 2

		left = servers_list[:midpoint]
		right = servers_list[midpoint:]

		def format_column(part, start_index):
			return "\n".join(f"{i + start_index}. {list(server.keys())[0]}" for i, server in enumerate(part))
		
		embed = discord.Embed(title="servers", description="total: {}".format(total), color=default_color)
		embed.add_field(name="", value=(f">>> {format_column(left, 1)}"))
		embed.add_field(name="", value=(f">>> {format_column(right, midpoint + 1)}"))

		await ctx.send(embed=embed)
		await ctx.message.delete()

	@server.command(name="rename", aliases=["ren"], help="rename a server")
	@app_commands.describe(old_name="server to rename", new_name="new server name")
	async def rename_server(self, ctx, old_name: str, *, new_name: str):
		data = json_load()
		servers_list = data.get("servers_list", [])

		for i, entry in enumerate(servers_list):
			if old_name in entry:
				value = entry[old_name]
				servers_list[i] = {new_name: value}
				data["servers_list"] = servers_list
				json_save(data)
				await ctx.send(f"renamed server `{old_name}` to `{new_name}`")
				return

		await ctx.send(f"server `{old_name}` doesn't exist")

	# server nuke
	@server.command(name="nuke", help="nukes data")
	@app_commands.describe(target="options: servers, messages(msgs), separator_config or * for all")
	async def nuke(self, ctx, target: str):
		target = target.lower()

		if target not in ["servers", "messages", "msgs", "*"]:
			await ctx.send("invalid target: servers, messages (msgs), separator_config or * for all")
			return

		# load json
		data = json_load()
		
		if target == "*":
			data["servers_list"] = []
			data["messages_list"] = []
			data["separator_config"] = {}
		elif target == "servers":
			data["servers_list"] = []
		elif target in["messages", "msgs"]:
			data["messages_list"] = []
		elif target == "serparator_config":
			data["separator_config"] = {}

		# save json
		json_save(data)

		await ctx.send(f"nuked `{'all data for server (lmao)' if target == '*' else target}`")

	# server separator
	@server.command(name="separator", aliases=["sep"], help="change separator options | preview separator config")
	@app_commands.describe(enabled="enable separators true/false", edges="include edges (above top/below bottom) true/false)", style="content of separator")
	async def separators(self, ctx, enabled: str = None, edges: str = None, *, style: str = None):
		
		if enabled is not None:enabled = enabled.lower() in ('true', 'yes', '1', 'on')
		if edges is not None:edges = edges.lower() in ('true', 'yes', '1', 'on')

		# load json
		data = json_load()
		config = data.setdefault("separator_config", {
			"enabled": True,
			"edges": True,
			"style": "••••••••••••••••••••••••••••••••••••••••••••••••••••"
		})

		if enabled is None and edges is None and style is None:
			await ctx.send(f"{config['style']}\nseparator is {'`enabled`' if config['enabled'] else '`disabled`'} and edges are {'`included`' if config['edges'] else '`excluded`'}\n{config['style']}")
			return

		if enabled is not None:
			config["enabled"] = enabled
		if edges is not None:
			config["edges"] = edges
		if style is not None and style.strip():
			config["style"] = style.strip()

		data["separator_config"] = config
		json_save(data)

		await ctx.send("updated separators\n-# deleting..", delete_after=3)

	# server initiate, send all the server messages
	@server.command(name="initiate", aliases=["i"], help="initiate/update all server messages")
	@commands.bot_has_permissions(manage_messages=True, read_message_history=True)
	async def initiate(self, ctx: Context):
		
		await ctx.message.delete()

		# load json
		data = json_load()

		# load dicts
		servers_list = data.get("servers_list", [])
		messages_list = data.get("messages_list", [])

		sep_config = data.get("separator_config", {})
		use_separators = sep_config.get("enabled", True)
		include_edges = sep_config.get("edges", True)
		separator_text = sep_config.get("style", "••••••••••••••••••••••••••••••••••••••••••••••••••••")

		# load keys from dicts
		server_contents = [list(entry.values())[0] for entry in servers_list]
		message_sequence: list[Tuple[str. str]] = build_message_sequences(server_contents, separator_text, use_separators, include_edges)
		
		edited = 0
		added = 0
		msgs_deleted = 0
		idx = 0

		progress_msg = await ctx.send(f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")

		while idx < len(message_sequence):
			msg_type, content = message_sequence[idx]

			# if theres a message id at current index
			try:
				message_id = messages_list[idx]
				message = await ctx.channel.fetch_message(int(message_id))

				# comparing content of existing msg vs stored msg
				if message.content.strip() != content.strip():
					# content mismatch, fix mismatch (overwrite)
					await message.edit(content=content)
					edited += 1
					await progress_msg.edit(content=f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")
					

			# no msg at current index, create a new one
			except IndexError:
				new_message = await ctx.send(content)
				added += 1
				# save id to messages_list
				messages_list.append(str(new_message.id))
				await progress_msg.edit(content=f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")

			# initiated message deleted (i forgot how this logic works in its entirety so i have nothing to explain here)
			except discord.NotFound:
				# message doesn't exist, delete broken msg id
				del messages_list[idx]

				# save json
				data["messages_list"] = messages_list
				json_save(data)
				await progress_msg.edit(content=f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")
				
				continue
			
			idx += 1
			
		# remove useless messages
		if len(messages_list) > len(message_sequence):
			excess_ids = messages_list[len(message_sequence):]
			for msg_id in excess_ids:
				try:
					message = await ctx.channel.fetch_message(int(msg_id))
					await message.delete()
					msgs_deleted += 1
					await progress_msg.edit(content=f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")
				except discord.NotFound:
					pass
			
			messages_list = messages_list[:len(message_sequence)]

		# save json
		data["messages_list"] = messages_list
		json_save(data)

		await progress_msg.delete()
		
		if edited == 0 and added == 0 and msgs_deleted == 0:
			await ctx.send(">>> no changes made")
		else:
			await ctx.send(f">>> {added} added\n{edited} edited\n{msgs_deleted} msgs deleted")

	# server move
	@server.command(name="move", aliases=["m"], help="move server in list")
	@app_commands.describe(name="server to move", action="mode of moving, options: up, down, to, above, below", target="by X amount, to Xth position, above/below X server")
	async def mv(self, ctx, name: str, action: str, target: str):
		name = name.lower().strip()
		action = action.lower().strip()

		# load json
		data = json_load()
		servers_list = data.get("servers_list", [])

		index = calc_index(servers_list, name)

		if index is None:
			return await ctx.send(f"server `{name}` doesn't exist")
		
		if action not in ("up", "u", "down", "d", "to", "t", "above", "a", "below", "b"):
			return await ctx.send(f"invalid action, options: up, down, to, above, below")

		amount = None

		# move up
		if action in ("up", "u"):
			action = "up"
			server = servers_list.pop(index)
			amount = int(target)
			
			# calculate new position
			new_index = max(index - amount, 0)

		elif action in ("down", "d"):
			action = "down"
			server = servers_list.pop(index)
			amount = int(target)

			# calculate new position
			new_index = index + amount

		elif action in ("to", "t"):
			action = "to"
			server = servers_list.pop(index)
			amount = int(target)

			# ensure target index is within bounds
			# new_index = max(0, min(amount -1, len(servers_list) - 1))
			new_index = amount - 1

		elif action in ("above", "a"):
			action = "above"
			server = servers_list.pop(index)
			# find target index
			target_index = calc_index(servers_list, target.lower())
			if target_index is None:return await ctx.send(f"server `{target}` doesn't exist")
			new_index = target_index
			
		elif action in ("below", "b"):
			action = "below"
			server = servers_list.pop(index)
			# find index
			target_index = calc_index(servers_list, target.lower())
			if target_index is None:return await ctx.send(f"server `{target}` doesn't exist")
			new_index = target_index +1 if index < target_index else target_index +1
		
		# insert server at new position
		servers_list.insert(new_index, server)
			
		# save json
		data["servers_list"] = servers_list
		json_save(data)

		msg = f"server `{name}` moved {action}"
		if action in ("up", "u", "down", "d"):
			msg += f" by {amount}"
		elif action in ("to", "t"):
			msg += f" {target} position"
		else:
			msg += f" `{target}`"
		await ctx.send(msg)
			
	# server import (group)
	@server.group(name="import", help="import messages as server")
	async def ximport(self, ctx):
		if ctx.invoked_subcommand is None:
			return await ctx.send("use import subcommands: as, bulk")

	# server import as
	@ximport.command(name="as", help="import replied message as a server message for prefix cmd, for app cmd use msg id")
	@app_commands.describe(name="server name", message_id="id of message to import")
	async def xas(self, ctx, *, name: str, message_id: str = None):
		if ctx.interaction is None:
			if ctx.message.reference:
				replied_message_id = ctx.message.reference.message_id
				replied_message = await ctx.channel.fetch_message(replied_message_id)
				server_content = replied_message.content

				# load json
				data = json_load()
				
				servers_list = data.get("servers_list", [])
				# check if server exists, replace its value
				for entry in servers_list:
					if name in entry:
						entry[name] = server_content
						break
				else:
					# not found append
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
				# check if server exists, replace its value
				for entry in servers_list:
					if name in entry:
						entry[name] = app_server_content
						break
				else:
					# not found append
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
		final_messages = []
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
			await ctx.send("no server messages imported")
			return

		naming_msg = await ctx.send("starting bulk naming..")

		for msg in reversed(collected_messages):
			await naming_msg.edit(content=f"{msg.content}")

			def check(m):
				return m.author == ctx.author and m.channel == ctx.channel
		
			try:
				reply = await self.bot.wait_for("message", check=check, timeout=60)
				final_messages.append({reply.content: msg.content})
				await asyncio.sleep(0.5)
				await reply.delete()
			except asyncio.TimeoutError:
				await ctx.send("timed out waiting for name response, import terminated")
				return

		# load json
		data = json_load()

		servers_list = data.setdefault("servers_list", [])

		# check for duplicates

		# flatten existing lsit into a dict
		merged = {list(entry.keys())[0]: list(entry.values())[0] for entry in servers_list}

		# add/replace with final_messages
		for entry in final_messages:
			key = list(entry.keys())[0]
			value = list(entry.values())[0]
			merged[key] = value

		# add collected message to list
		data["servers_list"] = [{k: v} for k, v in merged.items()]

		# save json
		json_save(data)

		await naming_msg.edit(content=f"successfully imported {len(collected_messages)} messages")

async def setup(bot):
	await bot.add_cog(server(bot))