import os, aiosqlite
from pathlib import Path

async def init_db(bot):
	os.makedirs("assets", exist_ok=True)
	bot.db = await aiosqlite.connect(os.path.join("assets", "main.db"))
	await bot.db.execute("PRAGMA journal_mode=WAL")

	await apply_schemas(bot.db)
	
SCHEMA_PATH = Path(__file__).parent / "schemas.sql"

async def apply_schemas(db):

	with SCHEMA_PATH.open("r", encoding="utf-8") as f:
		schema = f.read()
	await db.executescript(schema)
	await db.commit()