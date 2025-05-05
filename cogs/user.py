import discord, uuid, yt_dlp, os, mimetypes
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands, interactions
from utils.values import default_color

class user(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")
	
	# media
	@app_commands.command(name="media", description="preview media from a URL")
	@app_commands.allowed_installs(guilds=True, users=True)
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	async def media(self, interaction: discord.Interaction, url: str):
		await interaction.response.defer(thinking=True)

		if not url.startswith((
			"https://www.instagram.com/",
			"https://instagram.com/",
			"https://www.youtube.com/shorts/",
			"https://youtube.com/shorts/"
			)):
			return await interaction.followup.send(">>> platform not allowed, only: instagram reels or youtube shorts")

		uid = str(uuid.uuid4())
		filename = f"{uid}.%(ext)s"

		ydl_opts = {
			'outtmpl': filename,
			'format': 'bestvideo[ext=mp4]+bestaudio/best',
			'quiet': True,
			'merge_output_format': 'mp4',
		}

		try:
			with yt_dlp.YoutubeDL(ydl_opts) as ydl:
				info = ydl.extract_info(url, download=True)
				downloaded_filename = ydl.prepare_filename(info)
		except Exception as e:
			return await interaction.followup.send(f">>> failed to download media: {e}")

		if not os.path.exists(downloaded_filename):
			return await interaction.followup.send(">>> failed to fetch media")

		file_size = os.path.getsize(downloaded_filename)
		max_size = 25 * 1024 * 1024

		if file_size > max_size:
			os.remove(downloaded_filename)
			return await interaction.followup.send(">>> media file too large")

		mime_type, _ = mimetypes.guess_type(downloaded_filename)
		if not mime_type or not mime_type.startswith(("video", "image")):
			os.remove(downloaded_filename)
			return await interaction.followup.send(">>> unsupported media type")

		try:
			await interaction.followup.send(file=discord.File(downloaded_filename))
		finally:
			os.remove(downloaded_filename)
	
async def setup(bot):
	await bot.add_cog(user(bot))