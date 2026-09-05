import json
import os
from config import DATA_DIR

FILE = os.path.join(DATA_DIR, "users.json")


def load_users():
    try:
        with open(FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    fixed = {}
    for user_id, value in data.items():
        if isinstance(value, dict):
            fixed[user_id] = {"name": value.get("name", "Noma'lum")}
        else:
            fixed[user_id] = {"name": "Noma'lum"}
    return fixed


def save_users(users):
    with open(FILE, "w") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def add_user(user_id, name="Noma'lum"):
    users = load_users()
    if str(user_id) in users:
        return False
    users[str(user_id)] = {"name": name}
    save_users(users)
    return True


def delete_user(user_id):
    users = load_users()
    if str(user_id) not in users:
        return False
    del users[str(user_id)]
    save_users(users)
    return True


def update_name(user_id, name):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["name"] = name
        save_users(users)


def is_registered(user_id):
    users = load_users()
    return str(user_id) in users


def get_all_users():
    return load_users()
