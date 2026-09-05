import sqlite3
import os
from datetime import datetime
from config import DATA_DIR

DB_NAME = os.path.join(DATA_DIR, "attendance.db")


def connect():
    return sqlite3.connect(DB_NAME)


def create_table():
    db = connect()
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        date TEXT,
        time TEXT,
        UNIQUE(telegram_id, date)
    )
    """)
    db.commit()
    db.close()


def has_confirmed_today(telegram_id):
    today = datetime.now().strftime("%d.%m.%Y")
    db = connect()
    cursor = db.cursor()
    cursor.execute(
        "SELECT 1 FROM attendance WHERE telegram_id = ? AND date = ?",
        (telegram_id, today)
    )
    result = cursor.fetchone()
    db.close()
    return result is not None


def add_attendance(telegram_id):
    if has_confirmed_today(telegram_id):
        return False

    now = datetime.now()
    db = connect()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO attendance
        (telegram_id, date, time)
        VALUES (?, ?, ?)
        """,
        (
            telegram_id,
            now.strftime("%d.%m.%Y"),
            now.strftime("%H:%M")
        )
    )
    db.commit()
    db.close()
    return True


def get_today():
    today = datetime.now().strftime("%d.%m.%Y")
    db = connect()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT telegram_id, time
        FROM attendance
        WHERE date = ?
        """,
        (today,)
    )
    result = cursor.fetchall()
    db.close()
    return result
