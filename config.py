import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "kino_bot.db").strip()

def parse_owner_ids(value: str) -> set[int]:
    result = set()
    for item in value.split(","):
        item = item.strip()
        if item:
            try:
                result.add(int(item))
            except ValueError:
                continue
    return result

OWNER_IDS = parse_owner_ids(os.getenv("OWNER_IDS", ""))

if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN":
    raise RuntimeError("BOT_TOKEN .env faylida to'g'ri yozilmagan.")
if not OWNER_IDS:
    raise RuntimeError("OWNER_IDS .env faylida kamida bitta Telegram ID bo'lishi kerak.")
