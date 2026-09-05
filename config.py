import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6857995319

# Railway'da Volume ulanganda shu papkaga yozadi (masalan "/data")
# Volume bo'lmasa, joriy papkada saqlaydi (lokal ishlatish uchun)
DATA_DIR = os.getenv("DATA_DIR", ".")

# Papka mavjudligiga ishonch hosil qilamiz (Volume ulanganda ham,
# ulanmaganda ham) - aks holda fayl yozishda xato chiqishi mumkin
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"📁 DATA_DIR: {os.path.abspath(DATA_DIR)}")
except Exception as e:
    print(f"⚠️ DATA_DIR papkasini yaratib bo'lmadi: {e}")

if not BOT_TOKEN:
    print("❌ .env faylida (yoki Railway Variables'da) BOT_TOKEN yo'q!")
