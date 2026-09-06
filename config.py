import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [
    6857995319,
    7695822564  # 2-admin ID
]

DATA_DIR = os.getenv("DATA_DIR", ".")

try:
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"📁 DATA_DIR: {os.path.abspath(DATA_DIR)}")
except Exception as e:
    print(f"⚠️ DATA_DIR papkasini yaratib bo'lmadi: {e}")

if not BOT_TOKEN:
    print("❌ .env faylida (yoki Railway Variables'da) BOT_TOKEN yo'q!")
