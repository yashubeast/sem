from discord.ext import commands
import discord, json

async def handle_command_error(ctx, error):
	if isinstance(error, commands.MissingPermissions):
		await ctx.send(">>> your aah lacks perms to use this cmd")
	elif isinstance(error, commands.MissingRequiredArgument):
		await ctx.send(">>> missing a required arg\n-# deleting..", delete_after=3)
	elif isinstance(error, commands.BotMissingPermissions):
		await ctx.send(">>> i lack perms for ts :wilted_rose:")
	elif isinstance(error, FileNotFoundError):
		await ctx.send(">>> contact yasu, json file not found")
	elif isinstance(error, json.JSONDecodeError):
		await ctx.send(">>> contact yasu, error reading json file")
	elif isinstance(error, discord.Forbidden):
		await ctx.send(">>> contact yasu, bot lacks perms")
	elif isinstance(error, commands.CommandNotFound):
		return
	elif str(error).startswith("Role") and str(error).endswith("not found."):
		await ctx.send(f">>> role doesn't exist")
	else:
		if str(error).startswith("The check functions for command"):
			await ctx.send(">>> command not allowed for this aah server\n-# deleting..", delete_after=3)
		else:
			await ctx.send(f">>> :warning: error :warning: contact yasu ```py\n{error}```")