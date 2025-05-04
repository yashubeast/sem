import discord, json, os
from utils.json_handler import json_load

async def update_status(bot):
    # load the activity type and activity from the JSON config
	try:
		config = json_load("config")
		main_config = config.setdefault("main", {})

		activity_type_str = main_config.setdefault("activity_type", "watching")
		activity_text = main_config.setdefault("activity", "wall dry")

		activity_type_map = {
			"playing": discord.ActivityType.playing,
			"listening": discord.ActivityType.listening,
			"watching": discord.ActivityType.watching,
			"competing": discord.ActivityType.competing,
			"streaming": discord.ActivityType.streaming
		}
		activity_type = activity_type_map.get(activity_type_str, discord.ActivityType.watching)

		# set the bot's activity
		await bot.change_presence(
			activity=discord.Activity(
				type=activity_type,
				name=activity_text
			),
			status=discord.Status.online
		)

	except FileNotFoundError:
		print("config file not found.")
	except json.JSONDecodeError:
		print("error reading the config file.")