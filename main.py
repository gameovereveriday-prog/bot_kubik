import os
import random
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN не задан!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

pending_roll: dict[int, tuple] = {}


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Напиши <b>кубик</b> — и я брошу его за тебя.\n"
        "Второй участник тоже напишет <b>кубик</b> — и я рассужу, кто лох 😈"
    )


@dp.message(F.text.lower() == "кубик")
async def roll_dice(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name or "Аноним"
    username = message.from_user.username
    score = random.randint(1, 6)

    if chat_id not in pending_roll:
        pending_roll[chat_id] = (user_id, name, username, score)
        await message.reply(
            f"🎲 {name} выкинул <b>{score}</b>\n"
            f"⏳ Ждём соперника — пусть тоже напишет <b>кубик</b>"
        )
        return

    first_id, first_name, first_username, first_score = pending_roll.pop(chat_id)

    if first_id == user_id:
        pending_roll[chat_id] = (user_id, name, username, score)
        await message.reply(
            f"🎲 {name} перекинул: <b>{score}</b>\n⏳ Ждём соперника."
        )
        return

    if score < first_score:
        loser_id, loser_name, loser_username, loser_score = user_id, name, username, score
        winner_name, winner_score = first_name, first_score
    elif first_score < score:
        loser_id, loser_name, loser_username, loser_score = first_id, first_name, first_username, first_score
        winner_name, winner_score = name, score
    else:
        await message.reply(
            f"🎲 {first_name}: <b>{first_score}</b>\n"
            f"🎲 {name}: <b>{score}</b>\n\n"
            f"🤝 Ничья! Никто не лох. Перебрасывайте."
        )
        return

    if loser_username:
        mention = f"@{loser_username}"
    else:
        mention = f'<a href="tg://user?id={loser_id}">{loser_name}</a>'

    await message.reply(
        f"🎲 {first_name}: <b>{first_score}</b>\n"
        f"🎲 {name}: <b>{score}</b>\n\n"
        f"🏆 {winner_name} победил ({winner_score} против {loser_score})\n"
        f"😈 {mention} ты лох!"
    )


async def main():
    print("🚀 Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())