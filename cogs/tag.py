import discord, aiosqlite, os
from discord.ext import commands
from math import ceil
from discord import app_commands
from utils.values import checkadmin

class tag(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	# tag (group)
	@commands.hybrid_group(help="preview a tag", aliases=["t"])
	async def tag(self, ctx, *, name: str = None):
		subcommands = [cmd.name for cmd in ctx.command.commands]
		if name and name.lower() not in subcommands:
			async with self.bot.db.cursor() as cursor:
				await cursor.execute("SELECT content FROM tags WHERE name = ? AND (gid = -1 OR gid = ?) ORDER BY gid ASC limit 1", (name, ctx.guild.id))
				data = await cursor.fetchone()
				if data:
					await ctx.send(data[0])
				if data is None:
					await ctx.send(f"> tag `{name}` doesn't exist")

	# tag add
	@tag.command(name="add", aliases=["a"], help="add/replace tag")
	@app_commands.describe(name="name of the tag (case sensitive)", content="content for the tag")
	async def add(self, ctx: commands.Context, name: str, *, content: str = None):
		if content is None:
			if not ctx.message.reference:return await ctx.send("> please provide content for the tag or reply to a message containing the content")
			content = ctx.message.reference.resolved.content

		async with self.bot.db.cursor() as cursor:
			await cursor.execute("SELECT gid FROM tags WHERE name = ? AND (gid = ? or gid = -1)", (name, ctx.guild.id))
			data = await cursor.fetchone()

			if data is None:
				# add new tag
				await cursor.execute("INSERT INTO tags (name, content, gid, cid) VALUES (?, ?, ?, ?)", (name, content, ctx.guild.id, ctx.author.id))
				await ctx.send(f"> tag `{name}` created")
			else:
				existing_gid = data[0]

				# tag already exists, check user permissions
				if existing_gid != -1:
					if ctx.author.guild_permissions.manage_messages:
						await cursor.execute(
							"UPDATE tags SET content = ?, cid = ? WHERE name = ? AND gid = ?",
							(content, ctx.author.id, name, ctx.guild.id)
						)
						await ctx.send(f"> tag `{name}` updated")
					else:
						await ctx.send(f"> tag `{name}` already exists, you don't have permission to update it")
				elif existing_gid == -1:
					if checkadmin(ctx):
						await cursor.execute(
							"UPDATE tags SET content = ?, cid = ? WHERE name = ? AND gid = -1",
							(content, ctx.author.id, name)
						)
						await ctx.send(f"> global tag `{name}` updated")
					else:
						await ctx.send(f"> global tag `{name}` already exists, you don't have permission to update it")
			
			await self.bot.db.commit()

	# tag remove
	@tag.command(name="remove", aliases=["r", "rm"], help="remove a tag")
	@app_commands.describe(name="name of the tag to remove (case sensitive)")
	async def remove(self, ctx: commands.Context, name: str):
		async with self.bot.db.cursor() as cursor:
			await cursor.execute("SELECT gid, cid FROM tags WHERE name = ? AND (gid = ? or gid = -1)", (name, ctx.guild.id))
			data = await cursor.fetchone()

			if data is None:
				await ctx.send(f"> tag `{name}` doesn't exist")
			
			tag_gid, tag_owner_id = data

			if tag_gid == -1:
				# global tag
				if not checkadmin(ctx):
					return await ctx.send(f"> yo aah needs to be sem's admin for ts :wilted_rose:")
				await cursor.execute("DELETE FROM tags WHERE name = ? AND gid = -1", (name,))
				await ctx.send(f"> global tag `{name}` deleted")
			else:
				if ctx.author.id == tag_owner_id or ctx.author.guild_permissions.manage_messages:
					await cursor.execute("DELETE FROM tags WHERE name = ? AND gid = ?", (name, ctx.guild.id))
					await ctx.send(f"> tag `{name}` deleted")
				else:
					await ctx.send(f"> you don't have permission to delete tags")
			
			await self.bot.db.commit()

	# tag list
	@tag.command(name="list", aliases=["l"], help="list all tags")
	@app_commands.describe(query="global tags ? (default: false)")
	async def list(self, ctx: commands.Context, *, query: bool = False):
		async with self.bot.db.cursor() as cursor:
			if query:
				await cursor.execute("SELECT name FROM tags WHERE gid = -1")
			else:
				await cursor.execute("SELECT name FROM tags WHERE gid = ?", (ctx.guild.id,))
			data = await cursor.fetchall()
		if not data:
			await ctx.send("> no tags in server")
			return

		tag_list = "\n".join([tag[0] for tag in data])
		embed = discord.Embed(
			title="available tags",
			description=tag_list,
			color=discord.Color.from_rgb(241, 227, 226)
		)
		embed.set_footer(text=f"total tags: {len(data)}")
		await ctx.send(embed=embed, ephemeral=True)
	
	# tag global
	@tag.command(name="global", aliases=["g"], help="globalize a tag")
	@app_commands.describe(name="name of the tag to globalize (case sensitive)")
	async def xglobal(self, ctx: commands.Context, name: str):
		if not checkadmin(ctx):return await ctx.send("> yo aah needs to be sem's admin for ts :wilted_rose:")
		async with self.bot.db.cursor() as cursor:
			# check if a local or global version of the tag exists
			await cursor.execute("SELECT gid FROM tags WHERE name = ? AND (gid = ? OR gid = -1)", (name, ctx.guild.id))
			data = await cursor.fetchone()

			if data is None:
				return await ctx.send(f"> tag `{name}` doesn't exist in this guild or globally")

			current_gid = data[0]
			new_gid = -1 if current_gid != -1 else ctx.guild.id

			# perform the toggle
			await cursor.execute("UPDATE tags SET gid = ? WHERE name = ? AND gid = ?", (new_gid, name, current_gid))
			await ctx.send(f"> tag `{name}` is now {'global' if new_gid == -1 else 'local'}")

		await self.bot.db.commit()
	
async def setup(bot):
	await bot.add_cog(tag(bot))