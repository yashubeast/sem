import aiohttp

import discord, uuid, yt_dlp, os
from discord.ext import commands
from discord import app_commands

class user(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_ready(self):
		print(f"{__name__} is online!")

	# media
	@app_commands.command(name="media", description="preview media from a URL")
	@app_commands.allowed_installs(guilds=False, users=True)
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	async def media(self, interaction: discord.Interaction, url: str):
		await interaction.response.defer(thinking=True)

		if not url.startswith((
			"https://www.instagram.com/",
			"https://instagram.com/",

			"https://www.youtube.com/",
			"https://youtube.com/",

			"https://www.youtube.com/shorts/",
			"https://youtube.com/shorts/"
			)):
			return await interaction.followup.send("> platform not allowed\n-# allowed: youtube, instagram")

		uid = str(uuid.uuid4())
		filename = f"{uid}.%(ext)s"

		ydl_opts = {
			'outtmpl': filename,
			'format': 'best',
			'quiet': True,
		}

		max_size = 10 * 1024 * 1024
		catboxMOE = 100 * 1024 * 1024
		downloaded_filename = None

		try:
			with yt_dlp.YoutubeDL(ydl_opts) as ydl:
				info = ydl.extract_info(url, download=False)

				file_size = info.get('filesize') or info.get('filesize_approx') or 18*1024*1024
				file_size_mb = int(file_size/1024/1024) if file_size else None
				title = info.get('title') or None
				caption = (info.get('description') or '').strip()
				extractor = info.get('extractor') or None
				if extractor == "Instagram":
					lines = caption.splitlines()
					title = (lines[0].strip() + ('...' if len(lines) > 1 else '')).strip()

				# if not file_size:
					# return await interaction.followup.send('> could not determine file size')

				if file_size > catboxMOE:
					return await interaction.followup.send(f'> file size {int(file_size/1024/1024)}mb, max allowed 100mb')

				# if max_size < file_size < catboxMOE:
					# await interaction.followup.send(f'> downloading {file_size_mb}mb...')

				info = ydl.extract_info(url, download=True)
				downloaded_filename = ydl.prepare_filename(info)

				file_size = os.path.getsize(downloaded_filename)
				file_size_mb = file_size/1024/1024
		except:
			return await interaction.followup.send("> failed to download media")

		try:
			if file_size > max_size:

				# await interaction.edit_original_response(content='> uploading to litterbox...')
				url = "https://litterbox.catbox.moe/resources/internals/api.php"
				data = aiohttp.FormData()
				data.add_field("reqtype", "fileupload")
				data.add_field("time", "1h") # 1h, 12h, 24h, 72h
				data.add_field("fileToUpload", open(downloaded_filename, "rb"), filename=os.path.basename(downloaded_filename))

				async with aiohttp.ClientSession() as session:
					async with session.post(url, data=data) as resp:
						result = await resp.text()

				await interaction.edit_original_response(
					content=f'> {title}\n-# [source](<{url}>) | [litterbox]({result})'
				)

			else:
				# await interaction.followup.send(file=discord.File(downloaded_filename))
				await interaction.edit_original_response(
					content=f'> {title}\n-# [source](<{url}>)',
					attachments=[discord.File(downloaded_filename)]
				)
		except Exception as e:
			print(e)
			await interaction.edit_original_response(content='> error fetching video')
		finally:
			if downloaded_filename and os.path.exists(downloaded_filename):
				os.remove(downloaded_filename)

async def setup(bot):
	await bot.add_cog(user(bot))