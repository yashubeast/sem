import discord, aiosqlite
from discord.ext import commands
from math import ceil
from discord import app_commands

class tag(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
		self.bot.db = await aiosqlite.connect("assets/main.db")
		async with self.bot.db.cursor() as cursor:
			await cursor.execute("CREATE TABLE IF NOT EXISTS tags (name TEXT, content TEXT, guild INT, creator INT)")

	# tag (group)
	@commands.hybrid_group(help="commands for tags", aliases=["t"])
	async def tag(self, ctx, *, name: str = None):
		try:
			subcommands = [cmd.name for cmd in self.tag.commands]
			if name and name.lower() not in subcommands:
				async with self.bot.db.cursor() as cursor:
					await cursor.execute("SELECT content FROM tags WHERE guild = ? AND name = ?", (ctx.guild.id, name))
					data = await cursor.fetchone()
					if data:
						await ctx.send(data[0])
					if data is None:
						await ctx.send(f"tag `{name}`doesn't exist")

		except Exception as e:
			await ctx.send(f"error: {e}")

	# tag create
	@tag.command(name="create", aliases=["c"], help="create new tag")
	@app_commands.describe(name="name of the tag (case sensitive)", content="content for the tag")
	async def create(self, ctx: commands.Context, name: str, *, content: str):
		try:
			async with self.bot.db.cursor() as cursor:
				await cursor.execute("SELECT content FROM tags WHERE guild = ? AND name = ?", (ctx.guild.id, name))
				data = await cursor.fetchone()
				if data is None:
					await cursor.execute("INSERT INTO tags (name, content, guild, creator) VALUES (?, ?, ?, ?)", (name, content, ctx.guild.id, ctx.author.id))
					await ctx.send(f"tag `{name}` created")
				if data:
					await ctx.send(f"tag `{name}` already exists")
				
				await self.bot.db.commit()
		
		except Exception as e:
			await ctx.send(f"error: {e}")

	# tag delete
	@tag.command(name="delete", aliases=["d", "del"], help="delete existing tag")
	@app_commands.describe(name="name of the tag to delete (case sensitive)")
	@commands.has_permissions(manage_messages=True) # remove once logic added for only being able to delete ur own tags unless a admin
	async def tagdelete(self, ctx: commands.Context, name: str):
		try:
			async with self.bot.db.cursor() as cursor:
				await cursor.execute("SELECT name FROM tags WHERE guild = ? AND name = ?", (ctx.guild.id, name))
				data = await cursor.fetchone()
				if data:
					await cursor.execute("DELETE FROM tags WHERE name = ? AND guild = ?", (name, ctx.guild.id))
					await ctx.send(f"tag `{name}` deleted")
				else:
					await ctx.send(f"tag `{name}` doesn't exist")
				
				await self.bot.db.commit()
		
		except Exception as e:
			await ctx.send(f"error: {e}")

	# tag list
	@tag.command(name="list", aliases=["l"], help="list all tags")
	async def list(self, ctx: commands.Context):
		try:
			async with self.bot.db.cursor() as cursor:
				await cursor.execute("SELECT name FROM tags WHERE guild = ?", (ctx.guild.id,))
				data = await cursor.fetchall()
			if not data:
				await ctx.send("no tags in server")
				return

			tag_list = "\n".join([tag[0] for tag in data])
			embed = discord.Embed(
				title="available tags",
				description=tag_list,
				color=discord.Color.from_rgb(241, 227, 226)
			)
			embed.set_footer(text=f"total tags: {len(data)}")
			await ctx.send(embed=embed, ephemeral=True)

		except Exception as e:
			await ctx.send(f"error: {e}")
	
async def setup(bot):
	await bot.add_cog(tag(bot))