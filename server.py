from datetime import datetime, timedelta
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://spiffy-beignet-c2dfdc.netlify.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id TEXT UNIQUE,
    name TEXT,
    xp INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_done TEXT DEFAULT ''
)
""")
conn.commit()


def ensure_columns_exist():
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    if "telegram_id" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN telegram_id TEXT")
        conn.commit()

    if "streak" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
        conn.commit()

    if "last_done" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN last_done TEXT DEFAULT ''")
        conn.commit()


ensure_columns_exist()


class User(BaseModel):
    telegram_id: str
    name: str


class XPUser(BaseModel):
    telegram_id: str


@app.get("/")
def root():
    return {"message": "Server is working 🚀"}


@app.post("/login")
def login(user: User):
    cursor.execute(
        "SELECT id, telegram_id, name, xp, streak, last_done FROM users WHERE telegram_id=?",
        (user.telegram_id,),
    )
    existing = cursor.fetchone()

    if not existing:
        cursor.execute(
            "INSERT INTO users (telegram_id, name, xp, streak, last_done) VALUES (?, ?, ?, ?, ?)",
            (user.telegram_id, user.name, 0, 0, ""),
        )
    else:
        cursor.execute(
            "UPDATE users SET name=? WHERE telegram_id=?",
            (user.name, user.telegram_id),
        )

    conn.commit()
    return {"status": "ok"}


@app.post("/add_xp")
def add_xp(user: XPUser):
    cursor.execute(
        "SELECT xp, streak, last_done FROM users WHERE telegram_id=?",
        (user.telegram_id,),
    )
    result = cursor.fetchone()

    if not result:
        return {"error": "user not found"}

    xp, streak, last_done = result
    today = datetime.now().date()

    if last_done:
        last_date = datetime.strptime(last_done, "%Y-%m-%d").date()

        if last_date == today:
            return {
                "status": "already_done_today",
                "xp_gained": 0,
                "streak": streak,
                "bonus": 0,
                "xp_total": xp,
            }

        if today - last_date == timedelta(days=1):
            streak += 1
        else:
            streak = 1
    else:
        streak = 1

    base_xp = 10
    bonus = 0

    if streak >= 5:
        bonus = 100
        gained_xp = base_xp + bonus
        streak = 0
    else:
        gained_xp = base_xp

    xp += gained_xp

    cursor.execute(
        "UPDATE users SET xp=?, streak=?, last_done=? WHERE telegram_id=?",
        (xp, streak, today.strftime("%Y-%m-%d"), user.telegram_id),
    )
    conn.commit()

    return {
        "status": "ok",
        "xp_gained": gained_xp,
        "streak": streak,
        "bonus": bonus,
        "xp_total": xp,
    }


@app.get("/leaders")
def leaders():
    cursor.execute(
        "SELECT telegram_id, name, xp, streak FROM users ORDER BY xp DESC"
    )
    rows = cursor.fetchall()

    return [
        {
            "telegram_id": row[0],
            "name": row[1],
            "xp": row[2],
            "streak": row[3],
        }
        for row in rows
    ]


@app.get("/")
def root():
    return {"message": "Server is working 🚀"}