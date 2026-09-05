import json
import os
from datetime import datetime
from config import DATA_DIR

FILE = os.path.join(DATA_DIR, "voice_limit.json")
VOICE_LIMIT = 5


def _today():
    return datetime.now().strftime("%d.%m.%Y")


def load_data():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _get_entry(user_id):
    data = load_data()
    entry = data.get(str(user_id))
    today = _today()

    # Yangi kun boshlansa (yoki birinchi marta ishlatilsa) hisob 0 dan boshlanadi
    if not entry or entry.get("date") != today:
        entry = {"date": today, "count": 0, "warned": False}
        data[str(user_id)] = entry
        save_data(data)

    return data, entry


def has_warned_today(user_id):
    _, entry = _get_entry(user_id)
    return entry.get("warned", False)


def mark_warned(user_id):
    data, entry = _get_entry(user_id)
    entry["warned"] = True
    data[str(user_id)] = entry
    save_data(data)


def get_sent_count(user_id):
    _, entry = _get_entry(user_id)
    return entry.get("count", 0)


def can_send_voice(user_id):
    return get_sent_count(user_id) < VOICE_LIMIT


def increment_voice_count(user_id):
    data, entry = _get_entry(user_id)
    entry["count"] = entry.get("count", 0) + 1
    data[str(user_id)] = entry
    save_data(data)
    return entry["count"]


# --- Qaror kutilayotgan (hali yuborilmagan) ovozlar uchun doimiy saqlash ---
# Diskka yoziladi, shuning uchun server qayta ishga tushsa ham yo'qolmaydi.
PENDING_FILE = os.path.join(DATA_DIR, "pending_voice.json")


def _load_pending():
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_pending(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def set_pending_voice(user_id, file_id):
    data = _load_pending()
    data[str(user_id)] = file_id
    _save_pending(data)


def get_pending_voice(user_id):
    return _load_pending().get(str(user_id))


def clear_pending_voice(user_id):
    data = _load_pending()
    data.pop(str(user_id), None)
    _save_pending(data)
