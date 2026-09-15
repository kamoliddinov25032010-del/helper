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
    max_order = 0
    for user_id, value in data.items():
        if isinstance(value, dict):
            order = value.get("order")
            if isinstance(order, int):
                max_order = max(max_order, order)
            fixed[user_id] = {"name": value.get("name", "Noma'lum"), "order": order}
        else:
            fixed[user_id] = {"name": "Noma'lum", "order": None}

    # Eski (order maydoni bo'lmagan) foydalanuvchilarga tartib raqam beramiz
    changed = False
    for user_id, info in fixed.items():
        if info["order"] is None:
            max_order += 1
            info["order"] = max_order
            changed = True

    if changed:
        save_users(fixed)

    return fixed


def save_users(users):
    with open(FILE, "w") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def _next_order(users):
    orders = [info["order"] for info in users.values() if isinstance(info.get("order"), int)]
    return max(orders, default=0) + 1


def add_user(user_id, name="Noma'lum", order=None):
    users = load_users()
    if str(user_id) in users:
        return False

    max_possible = _next_order(users)

    if order is None or order > max_possible:
        order = max_possible
    elif order < 1:
        order = 1

    # Berilgan o'rindan boshlab qolgan foydalanuvchilarni bittaga suramiz
    for info in users.values():
        if info["order"] >= order:
            info["order"] += 1

    users[str(user_id)] = {"name": name, "order": order}
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


def get_all_users_sorted():
    users = load_users()
    return sorted(users.items(), key=lambda item: item[1].get("order", 0))
