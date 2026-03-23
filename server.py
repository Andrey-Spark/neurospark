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
    id INTEGER PRIMARY KEY,
    name TEXT,
    xp INTEGER
)
""")
conn.commit()

class User(BaseModel):
    name: str

@app.post("/login")
def login(user: User):
    cursor.execute("SELECT * FROM users WHERE name=?", (user.name,))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("INSERT INTO users (name, xp) VALUES (?, ?)", (user.name, 0))
        conn.commit()

    return {"status": "ok"}

@app.post("/add_xp")
def add_xp(user: User):
    cursor.execute("UPDATE users SET xp = xp + 10 WHERE name=?", (user.name,))
    conn.commit()
    return {"status": "xp added"}

@app.get("/leaders")
def leaders():
    cursor.execute("SELECT name, xp FROM users ORDER BY xp DESC")
    return cursor.fetchall()

@app.get("/")
def root():
    return {"message": "Server is working 🚀"}