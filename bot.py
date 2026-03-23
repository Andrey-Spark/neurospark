import asyncio
import json
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8593248257:AAFb425-wnTSMXaut5iLvW0sYsy7eyfwn00"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "data.json"

# ===== ЗАГРУЗКА =====
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_data()
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# ===== кнопка mini app =====
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Открыть приложение",
            web_app=WebAppInfo(url="https://твой-сайт.vercel.app")
        )],
        [InlineKeyboardButton(text="✅ Сделал", callback_data="done")],
        [InlineKeyboardButton(text="📊 Прогресс", callback_data="progress")],
        [InlineKeyboardButton(text="🏆 Лидеры", callback_data="leaders")]
    ])

# ===== КНОПКИ =====
def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сделал", callback_data="done")],
        [InlineKeyboardButton(text="🎯 Новое задание", callback_data="new_task")],
        [InlineKeyboardButton(text="📊 Прогресс", callback_data="progress")],
        [InlineKeyboardButton(text="🏆 Лидеры", callback_data="leaders")]
    ])

# ===== ЛОГИКА =====
def get_user(user_id):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"xp": 0, "streak": 0, "last_done": "", "completed": 0, "task": ""}
    return users[uid]

def get_level(xp):
    return xp // 50 + 1

def get_medal(xp):
    if xp >= 500:
        return "🏅 ЗОЛОТО"
    elif xp >= 200:
        return "🥈 СЕРЕБРО"
    elif xp >= 50:
        return "🥉 БРОНЗА"
    return "—"

def get_task(level):
    if level < 3:
        return random.choice(["10 отжиманий", "убери стол", "5 целей"])
    elif level < 6:
        return random.choice(["30 мин без телефона", "20 отжиманий", "начни сложную задачу"])
    else:
        return random.choice(["1 час работы", "50 отжиманий", "реши сложную проблему"])

# ===== КОМАНДЫ =====
@dp.message(Command("start"))
async def start(msg: types.Message):
    user = get_user(msg.from_user.id)
    task = get_task(get_level(user["xp"]))
    user["task"] = task
    save_data(users)

    await msg.answer(
        f"🔥 Твое задание:\n{task}",
        reply_markup=main_keyboard()
    )

# ===== CALLBACK ОБРАБОТКА =====
@dp.callback_query()
async def callbacks(call: types.CallbackQuery):
    user = get_user(call.from_user.id)

    # СДЕЛАЛ
    if call.data == "done":
        today = datetime.now().strftime("%Y-%m-%d")

        if user["last_done"]:
            last = datetime.strptime(user["last_done"], "%Y-%m-%d")
            if datetime.now() - last <= timedelta(days=1):
                user["streak"] += 1
            else:
                user["streak"] = 1
        else:
            user["streak"] = 1

        user["last_done"] = today

        xp = 10 + user["streak"] * 2
        user["xp"] += xp
        user["completed"] += 1

        save_data(users)

        await call.message.answer(
            f"✅ +{xp} XP\n🔥 Streak: {user['streak']}",
            reply_markup=main_keyboard()
        )

    # НОВОЕ ЗАДАНИЕ
    elif call.data == "new_task":
        task = get_task(get_level(user["xp"]))
        user["task"] = task
        save_data(users)

        await call.message.answer(
            f"🎯 Новое задание:\n{task}",
            reply_markup=main_keyboard()
        )

    # ПРОГРЕСС
    elif call.data == "progress":
        await call.message.answer(
            f"📊 XP: {user['xp']}\n"
            f"🏆 Уровень: {get_level(user['xp'])}\n"
            f"🔥 Streak: {user['streak']}\n"
            f"🎖️ Медаль: {get_medal(user['xp'])}",
            reply_markup=main_keyboard()
        )

    # ЛИДЕРЫ
    elif call.data == "leaders":
        top = sorted(users.items(), key=lambda x: x[1]["xp"], reverse=True)

        text = "🏆 Лидеры:\n\n"
        for i, (uid, data) in enumerate(top[:5], 1):
            text += f"{i}. {uid} — {data['xp']} XP\n"

        await call.message.answer(text, reply_markup=main_keyboard())

    await call.answer()

# ===== ЗАПУСК =====
async def main():
    print("Бот с кнопками запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())