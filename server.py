from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

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
    xp INTEGER DEFAULT 0
)
""")
conn.commit()


def ensure_column_exists():
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    if "telegram_id" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN telegram_id TEXT")
        conn.commit()


ensure_column_exists()


class User(BaseModel):
    telegram_id: str
    name: str


class XPUser(BaseModel):
    telegram_id: str


@app.post("/login")
def login(user: User):
    cursor.execute(
        "SELECT id, telegram_id, name, xp FROM users WHERE telegram_id=?",
        (user.telegram_id,),
    )
    existing = cursor.fetchone()

    if not existing:
        cursor.execute(
            "INSERT INTO users (telegram_id, name, xp) VALUES (?, ?, ?)",
            (user.telegram_id, user.name, 0),
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
        "UPDATE users SET xp = xp + 10 WHERE telegram_id=?",
        (user.telegram_id,),
    )
    conn.commit()
    return {"status": "xp added"}


@app.get("/leaders")
def leaders():
    cursor.execute(
        "SELECT telegram_id, name, xp FROM users ORDER BY xp DESC"
    )
    rows = cursor.fetchall()
    return [
        {"telegram_id": row[0], "name": row[1], "xp": row[2]}
        for row in rows
    ]


@app.get("/")
def root():
    return {"message": "Server is working 🚀"}