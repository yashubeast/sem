import os, aiosqlite

async def init_db(bot):
	os.makedirs("assets", exist_ok=True)
	bot.db = await aiosqlite.connect("assets/main.db")
	await bot.db.execute("PRAGMA journal_mode=WAL")

	async with bot.db.cursor() as cursor:
		await cursor.execute("""
			CREATE TABLE IF NOT EXISTS tags(
				name TEXT,
				content TEXT,
				gid INT,
				cid INT
			)
		""")
		await cursor.execute("""
			CREATE TABLE IF NOT EXISTS servers(
			 	pos INTEGER UNIQUE,
				name TEXT UNIQUE,
				content TEXT
			)
		""")
		await cursor.execute("""
			CREATE TABLE IF NOT EXISTS servers_msgs(
			pos INTEGER PRIMARY KEY,
			mid TEXT NOT NULL
			)
		""")
	
	await bot.db.commit()