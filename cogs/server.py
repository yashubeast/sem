import discord, json, os, asyncio
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands
from typing import Tuple
from utils.json_handler import json_load, json_save
from utils.values import default_color, checkserver

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

class server(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

		await self.bot.db.execute("""
			CREATE TABLE IF NOT EXISTS servers_sep (
				id INTEGER PRIMARY KEY CHECK (id = 1),
				enabled BOOLEAN NOT NULL DEFAULT 1,
				edges BOOLEAN NOT NULL DEFAULT 1,
				style TEXT NOT NULL DEFAULT '••••••••••••••••••••••••••••••••••••••••••••••••••••'
			)
		""")

	def cog_check(self, ctx):
		return checkserver(ctx)

	# server (group)
	@commands.hybrid_group(help="previews server", aliases=["s"])
	@commands.has_permissions(administrator=True)
	async def server(self, ctx, *, name: str = None):
		subcommand = [cmd.name for cmd in ctx.command.commands]

		if not name:
			await ctx.send(">>> provide server name to preview\n-# deleting..", delete_after=3)
			await ctx.message.delete()
			return

		name = name.lower().strip()

		if name not in subcommand:

			async with self.bot.db.execute("SELECT content FROM servers WHERE LOWER(name) = ?", (name,)) as cursor:
				row = await cursor.fetchone()
			
			if row is None:
				await ctx.send(f">>> server `{name}` doesn't exist\n-# deleting..", delete_after=3)
				await ctx.message.delete()
				return

			await ctx.send(row[0])
			await ctx.message.delete()

	# server add
	@server.command(name="add", aliases=["a"], help="add/overwrite a server")
	@app_commands.describe(name="server name")
	async def add(self, ctx, *, name: str):
		if ctx.interaction is None:
			if ctx.message.reference:
				replied_message_id = ctx.message.reference.message_id
				replied_message = await ctx.channel.fetch_message(replied_message_id)
				server_content = replied_message.content

				# check if server already exists
				async with self.bot.db.execute("SELECT 1 FROM servers WHERE name = ?", (name,)) as cursor:
					exists = await cursor.fetchone()

				# get current highest pos
				async with self.bot.db.execute("SELECT MAX(pos) FROM servers") as cursor:
					row = await cursor.fetchone()
					next_pos = (row[0] or 0) + 1
				
				async with self.bot.db.cursor() as cursor:
					await cursor.execute("""
						INSERT INTO servers (pos, name, content)
						VALUES (?, ?, ?)
						ON CONFLICT(name) DO UPDATE SET content=excluded.content
					""", (next_pos, name, server_content))
				await self.bot.db.commit()
				
				action = "replaced" if exists else "added"
				await ctx.send(f"server `{name}` {action}")
			else:
				await ctx.send("> you need to reply to a message")

	# server remove
	@server.command(name="remove", aliases=["r", "rm", "d", "del"], help="remove a server")
	@app_commands.describe(server="name of the server to remove")
	async def remove(self, ctx, *,server: str):
		
		server = server.lower().strip()

		async with self.bot.db.execute("SELECT pos FROM servers WHERE LOWER(name) =?", (server,)) as cursor:
			row = await cursor.fetchone()
		
		if not row:
			await ctx.send(f"server `{server}` doesn't exist")
			return
		
		deleted_pos = row[0]

		async with self.bot.db.cursor() as cursor:
			# delete the server
			await cursor.execute("DELETE FROM servers WHERE pos = ?", (deleted_pos,))

			# shift positions up for all entries below the deleted one
			await cursor.execute("""
				UPDATE servers
				SET pos = pos - 1
				WHERE pos > ?
			""", (deleted_pos,))
		
		await self.bot.db.commit()

		await ctx.send(f"server `{server}` removed")

	# server list
	@server.command(name="list", aliases=["l"], help="list all servers")
	async def list(self, ctx: Context):
		
		async with self.bot.db.execute("SELECT name FROM servers ORDER BY pos") as cursor:
			rows = await cursor.fetchall()
		
		if not rows:
			return await ctx.send("no servers in list")

		servers_list = [row[0] for row in rows]
		total = len(servers_list)
		midpoint = total // 2 + total % 2

		left = servers_list[:midpoint]
		right = servers_list[midpoint:]

		def format_column(part, start_index):
			return "\n".join(f"{i + start_index}. {name}" for i, name in enumerate(part))
		
		embed = discord.Embed(title="servers", description="total: {}".format(total), color=default_color)
		embed.add_field(name="", value=(f">>> {format_column(left, 1)}"))
		embed.add_field(name="", value=(f">>> {format_column(right, midpoint + 1)}"))

		await ctx.send(embed=embed)
		await ctx.message.delete()

	# server rename
	@server.command(name="rename", aliases=["ren"], help="rename a server")
	@app_commands.describe(old_name="server to rename", new_name="new server name")
	async def rename_server(self, ctx, old_name: str, *, new_name: str):
		old_name = old_name.lower().strip()
		new_name = new_name.lower().strip()

		# check if old name exists
		async with self.bot.db.execute("SELECT 1 FROM servers WHERE LOWER(name) = ?", (old_name,)) as cursor:
			exists = await cursor.fetchone()
		if not exists:
			await ctx.send(f"server `{old_name}` doesn't exist")
			return
		
		# check if new name alr exists
		async with self.bot.db.execute("SELECT 1 FROM servers WHERE LOWER(name) = ?", (new_name,)) as cursor:
			exists_new = await cursor.fetchone()
		if exists_new:
			await ctx.send(f"server `{new_name}` already exists, choose a different name")
			return

		# perform ren
		await self.bot.db.execute(
			"UPDATE servers SET name = ? WHERE LOWER(name) = ?", (new_name, old_name)
		)
		await self.bot.db.commit()

		await ctx.send(f"renamed server `{old_name}` to `{new_name}`")

	# server nuke
	@server.command(name="nuke", help="nukes data")
	@app_commands.describe(target="options: servers, messages(msgs), separator_config or * for all")
	async def nuke(self, ctx, target: str):
		target = target.lower()

		if target not in ["servers", "messages", "msgs", "*"]:
			await ctx.send("> invalid target: servers, messages (msgs), separator_config(sep) or * for all")
			return

		nuked = []
		
		if target == "*":
			await self.bot.db.execute("DELETE FROM servers")
			await self.bot.db.execute("DELETE FROM servers_msgs")
		elif target == "servers":
			await self.bot.db.execute("DELETE FROM servers")
		elif target in["messages", "msgs"]:
			await self.bot.db.execute("DELETE FROM servers_msgs")
		elif target in["serparator_config", "sep"]:
			await self.bot.db.execute("DELETE FROM servers_sep")

		await self.bot.db.commit()

		await ctx.send(f"nuked `{'all data for server (lmao)' if target == '*' else target}`")

	# server separator
	@server.command(name="separator", aliases=["sep"], help="change separator options | preview separator config")
	@app_commands.describe(enabled="enable separators true/false", edges="include edges (above top/below bottom) true/false)", style="content of separator")
	async def separators(self, ctx, enabled: str = None, edges: str = None, *, style: str = None):
		
		if enabled is not None:enabled = enabled.lower() in ('true', 'yes', '1', 'on')
		if edges is not None:edges = edges.lower() in ('true', 'yes', '1', 'on')

		# get current config or insert default if not present
		async with self.bot.db.cursor() as cursor:
			await cursor.execute("SELECT enabled, edges, style FROM servers_sep WHERE id = 1")
			row = await cursor.fetchone()

			if row is None:
				# insert default config
				default_config = (1, 1, "••••••••••••••••••••••••••••••••••••••••••••••••••••")
				await cursor.execute("INSERT INTO servers_sep (id, enabled, edges,style) VALUES (1, ?, ?, ?)", default_config)
				enabled_val, edges_val, style_val = default_config
			else:
				enabled_val, edges_val, style_val = row

		# update values based on user input
		enabled_val = enabled if enabled is not None else enabled_val
		edges_val = edges if edges is not None else edges_val
		style_val = style.strip() if style is not None and style.strip() else style_val

		# update db
		await self.bot.db.execute("""
			INSERT INTO servers_sep (id, enabled, edges, style)
			VALUES (1, ?, ?, ?)
			ON CONFLICT(id) DO UPDATE SET enabled = excluded.enabled, edges = excluded.edges, style = excluded.style
		""", (enabled_val, edges_val, style_val))

		await self.bot.db.commit()

		if enabled is None and edges is None and style is None:
			await ctx.send(f"{style_val}\nseparator is {'`enabled`' if enabled_val else '`disabled`'} and edges are {'`included`' if edges_val else '`excluded`'}\n{style_val}")
		else:
			await ctx.send("updated separators\n-# deleting..", delete_after=3)

	# server initiate, send all the server messages
	@server.command(name="initiate", aliases=["i"], help="initiate/update all server msgs, don't use app-cmd")
	@commands.bot_has_permissions(manage_messages=True, read_message_history=True)
	async def initiate(self, ctx: Context, *, query: str = None):
		
		await ctx.message.delete()

		# fetch servers
		async with self.bot.db.cursor() as cursor:
			await cursor.execute("SELECT pos, name, content FROM servers ORDER BY pos")
			servers = await cursor.fetchall()

			# fetch sep config
			await cursor.execute("SELECT enabled, edges, style FROM servers_sep WHERE id = 1")
			sep_row = await cursor.fetchone()
			if sep_row is None:
				# default is not set
				enabled_val, edges_val, style_val = True, True, "••••••••••••••••••••••••••••••••••••••••••••••••••••"
			else:
				enabled_val, edges_val, style_val = sep_row
			
			# fetch stored msg ids
			await cursor.execute("SELECT pos, mid FROM servers_msgs ORDER BY pos")
			stored_msgs = await cursor.fetchall()
		
		# build sequence with sep
		server_contents = [content for _, _, content in servers]
		message_sequence: list[Tuple[str, str]] = build_message_sequences(server_contents, style_val, enabled_val, edges_val)
		stored_msg_dict = {pos: mid for pos, mid in stored_msgs}
		
		# if specified
		if query is not None:
			query = query.strip().lower()
			name_to_pos = {name.lower(): pos for pos, name, _ in servers}

			if query not in name_to_pos:return await ctx.send(f"> no server named `{query}`")

			# calculate msg index for server
			server_index = name_to_pos[query]
			msg_idx = server_index
			if enabled_val:
				if edges_val:
					msg_idx += 1
				msg_idx += server_index - 2
			
			msg_type, new_content = message_sequence[msg_idx]
			message_id = stored_msg_dict.get(msg_idx + 1)

			try:
				if message_id:
					message = await ctx.channel.fetch_message(int(message_id))
					if message.content.strip() != new_content.strip():
						await message.edit(content=new_content)
						return await ctx.send(f"update content for `{query}`")
					else:
						return await ctx.send(f"no changes needed for `{query}`")
				else:
					raise discord.NotFound
			except discord.NotFound:
				return await ctx.send(f"missing msg for `{query}`")

		edited = 0
		added = 0
		msgs_deleted = 0
		idx = 0

		progress_msg = await ctx.send(f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")

		while idx < len(message_sequence):
			msg_type, content = message_sequence[idx]

			# if theres a message id at current index
			try:
				message_id = stored_msg_dict.get(idx + 1)
				if message_id is not None:
					message = await ctx.channel.fetch_message(int(message_id))

					# comparing content of existing msg vs stored msg
					if message.content.strip() != content.strip():
						# content mismatch, fix mismatch (overwrite)
						await message.edit(content=content)
						edited += 1
						await progress_msg.edit(content=f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")
				else:
					raise IndexError
					

			# no msg at current index, create a new one
			except (IndexError, discord.NotFound):
				new_message = await ctx.send(content)
				added += 1
				await progress_msg.edit(content=f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")

				async with self.bot.db.cursor() as cursor:
					await cursor.execute("""
						INSERT INTO servers_msgs (pos, mid)
						VALUES (?, ?)
						ON CONFLICT(pos) DO UPDATE SET mid=excluded.mid
					""", (idx + 1, str(new_message.id)))
				await self.bot.db.commit()
			
			idx += 1
			
		# remove useless messages
		if len(stored_msgs) > len(message_sequence):
			excess_positions = [pos for pos, _ in stored_msgs if pos > len(message_sequence)]
			for pos in excess_positions:
				try:
					mid = stored_msg_dict[pos]
					message = await ctx.channel.fetch_message(int(mid))
					await message.delete()
					msgs_deleted += 1
					await progress_msg.edit(content=f">>> initiating.. ({added} added/ {edited} edited / {msgs_deleted} deleted)")
				except discord.NotFound:
					pass
			
				# remove from db
				async with self.bot.db.cursor() as cursor:
					await cursor.execute("DELETE FROM servers_msgs WHERE pos = ?", (pos,))
				await self.bot.db.commit()
		
		await progress_msg.delete()

		if edited == 0 and added == 0 and msgs_deleted == 0:
			await ctx.send(">>> no changes made")
		else:
			await ctx.send(f">>> {added} added\n{edited} edited\n{msgs_deleted} msgs deleted")

	# server move
	@server.command(name="move", aliases=["m"], help="move server in list")
	@app_commands.describe(name="server to move", action="mode of moving, options: up, down, to, above, below", target="by X amount, to Xth position, above/below X server")
	async def mv(self, ctx, name: str = None, action: str = None, target: str = None):
		name = name.lower().strip() if name is not None else None
		action = action.lower().strip() if action is not None else None

		if name is None:
			return await ctx.send("> provide server name to move")

		if action not in ("up", "u", "down", "d", "to", "t", "above", "a", "below", "b"):
			return await ctx.send(f"> available options for moving server: `up`, `down`, `to`, `above`, `below`")

		if target is None:
			return await ctx.send("> provide target amount or position to move to")

		# get current pos of the server
		async with self.bot.db.execute("SELECT pos FROM servers WHERE LOWER(name) = ?", (name,)) as cursor:
			row = await cursor.fetchone()
		
		if row is None:
			return await ctx.send(f"> server `{name}` doesn't exist")

		cur_pos = row[0]

		# get total count of servers
		async with self.bot.db.execute("SELECT COUNT(*) FROM servers") as cursor:
			total_servers = (await cursor.fetchone())[0]
		
		# helper to get pos of a server (used for above/below)
		async def get_pos(server_name):
			async with self.bot.db.execute("SELECT pos FROM servers WHERE LOWER(name) = ?", (server_name.lower(),)) as cursor:
				result = await cursor.fetchone()
				return result[0] if result else None
		
		# calculate new_pos based on action

		if action in ("up", "u"):
			action = "up"
			try:
				amount = int(target)
			except ValueError:
				return await ctx.send("> target must be an integer for `up` action")
			new_pos = max(cur_pos - amount, 1)

		elif action in ("down", "d"):
			action = "down"
			try:
				amount = int(target)
			except ValueError:
				return await ctx.send("> target must be an integer for `down` action")
			new_pos = min(cur_pos + amount, total_servers)

		elif action in ("to", "t"):
			action = "to"
			try:
				amount = int(target)
			except ValueError:
				return await ctx.send("> target must be an integer for `to` action")
			if not (1 <= amount <= total_servers):
				return await ctx.send(f"> target pos must be between 1 and {total_servers}") # CHANGE THIS
			new_pos = amount

		elif action in ("above", "a"):
			action = "above"
			target_pos = await get_pos(target)
			if target_pos is None:
				return await ctx.send(f"> server `{target}` doesn't exist")
			new_pos = target_pos
			if cur_pos < target_pos:
				new_pos -= 1
			
		elif action in ("below", "b"):
			action = "below"
			target_pos = await get_pos(target)
			if target_pos is None:
				return await ctx.send(f"> server `{target}` doesn't exist")
			new_pos = target_pos + 1
			if cur_pos < target_pos:
				new_pos -= 1
			if new_pos > total_servers:
				new_pos = total_servers

		else:
			return await ctx.send("> invalid action, use `up`, `down`, `to`, `above`, `below`")
		
		if new_pos == cur_pos:
			return await ctx.send("> server is already in that position")
		
		async with self.bot.db.cursor() as cursor:
			
			# fetch server order by pos
			await cursor.execute("SELECT name FROM servers ORDER by pos")
			servers = [row[0] for row in await cursor.fetchall()]

			# reorder the list
			if name not in servers:
				return
			servers.remove(name)
			servers.insert(new_pos - 1, name)

			# reassign new positions
			for i, server_name in enumerate(servers, start=1):
				await cursor.execute("UPDATE servers set pos = ? WHERE name = ?", (-1000 - i, server_name))

			for i, server_name in enumerate(servers, start=1):
				await cursor.execute("UPDATE servers SET pos = ? WHERE name = ?", (i, server_name))
		
		await self.bot.db.commit()

		await ctx.send(f"> moved server `{name}` {action} to position `{new_pos}`")

	# server import
	@server.command(name="import", help="bulk import server messages using range")
	@app_commands.describe(from_id="bottom message_id of range", to_id="top message_id of range", user="specify user to look messages of", exclude="content to be excluded")
	async def ximport(self, ctx, from_id: str, to_id: str, user: discord.User = None, exclude: str = None):
		collected_messages = []
		final_messages = []
		found_from = False

		async for message in ctx.channel.history(limit=None, oldest_first=False):

			if user and message.author.id != user.id:
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
			await ctx.send(">>> no server messages imported")
			return

		# if no exclude text provided, ask for it
		if exclude is None:
			exclude_prompt = await ctx.send(">>> reply to a message to be excluded (usually separator msg) or type `skip` to exclude nothing")
		
		def reply_check(m):
			return m.author == ctx.author and m.channel == ctx.channel

		try:
			reply = await self.bot.wait_for("message", check=reply_check, timeout=60)

			if reply.content.lower() != "skip" and reply.reference:
				replied_message = await ctx.channel.fetch_message(reply.reference.message_id)
				exclude = replied_message.content
				await ctx.send(f">>> messages containing this will be excluded: `{exclude}`\n-# deleting..", delete_after=5)
			elif reply.content.lower() == "skip":
				await ctx.send(">>> no messages will be excluded\n-# deleting..", delete_after=5)
			else:
				await ctx.send(">>> invalid reply or no reference, continuing without excluding messages\n-# deleting..", delete_after=5)
		except asyncio.TimeoutError:
			await ctx.send(">>> timed out waiting for exclude message, continuing without excluding\n-# deleting..", delete_after=5)

		if exclude:
			collected_messages = [m for m in collected_messages if exclude not in m.content]
		await exclude_prompt.delete()
		naming_msg = await ctx.send(">>> starting bulk naming..")

		for msg in reversed(collected_messages):
			await naming_msg.edit(content=f"{msg.content}")

			def check(m):
				return m.author == ctx.author and m.channel == ctx.channel
		
			try:
				reply = await self.bot.wait_for("message", check=check, timeout=60)
				if reply.content.lower() == "skip":
					await asyncio.sleep(0.5)
					await reply.delete()
					continue
				final_messages.append({reply.content: msg.content})
				await asyncio.sleep(0.5)
				await reply.delete()
			except asyncio.TimeoutError:
				await ctx.send("timed out waiting for name response, import terminated")
				return

		# insert into servers table
		async with self.bot.db.cursor() as cursor:
			# get current max pos
			await cursor.execute("SELECT MAX(pos) FROM servers")
			row = await cursor.fetchone()
			start_pos = (row[0] or 0) + 1

			# prepare inserts
			for entry in final_messages:
				name = list(entry.keys())[0]
				content = list(entry.values())[0]
				
				# check if name exists
				await cursor.execute("SELECT pos FROM servers WHERE name = ?", (name,))
				row = await cursor.fetchone()

				if row:
					# update content
					await cursor.execute(
						"UPDATE servers SET content = ? WHERE name = ?",
						(content, name)
					)
				else:
					# insert with new pos
					await cursor.execute(
						"INSERT INTO servers (pos, name, content) VALUES (?, ?, ?)",
						(start_pos, name, content)
					)
					start_pos += 1
		
		await self.bot.db.commit()
		await naming_msg.edit(content=f"> successfully imported {len(final_messages)}")

async def setup(bot):
	await bot.add_cog(server(bot))