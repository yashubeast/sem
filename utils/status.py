import discord, json, os

json_path = "assets/config.json"

def ensure_json():
	os.makedirs(os.path.dirname(json_path), exist_ok=True)
	if not os.path.isfile(json_path):
		with open(json_path, "w", encoding="utf-8") as f:
			json.dump({}, f, indent=4)

def json_load():
	ensure_json()
	with open(json_path, "r", encoding="utf-8") as f:
		return json.load(f)

async def update_status(bot):
    # load the activity type and activity from the JSON config
	try:
		config = json_load()
		main_config = config.get("main", {})

		activity_type_str = main_config.get("activity_type", "playing").lower()
		activity_text = main_config.get("activity", "with code")

		activity_type_map = {
			"playing": discord.ActivityType.playing,
			"listening": discord.ActivityType.listening,
			"watching": discord.ActivityType.watching,
			"competing": discord.ActivityType.competing,
			"streaming": discord.ActivityType.streaming
		}
		activity_type = activity_type_map.get(activity_type_str, discord.ActivityType.playing)

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