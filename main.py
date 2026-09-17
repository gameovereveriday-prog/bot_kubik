import os
import random
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from database import init_db, record_result, get_user_stats, get_top_stats

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN не задан!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

pending_roll: dict[int, tuple] = {}


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Напиши <b>кубик</b> — и я брошу его за тебя.\n\n"
        "Команды:\n"
        "/stats — твоя статистика побед и поражений\n"
        "/topstats — топ чата по победам"
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

    # Ничья
    if first_score == score:
        await record_result(chat_id, first_id, first_name, "draw")
        await record_result(chat_id, user_id, name, "draw")
        await message.reply(
            f"🎲 {first_name}: <b>{first_score}</b>\n"
            f"🎲 {name}: <b>{score}</b>\n\n"
            f"🤝 Ничья! Никто не лох. Перебрасывайте."
        )
        return

    # Определяем победителя и проигравшего
    if score < first_score:
        loser_id, loser_name, loser_username, loser_score = user_id, name, username, score
        winner_id, winner_name, winner_username, winner_score = first_id, first_name, first_username, first_score
    else:
        loser_id, loser_name, loser_username, loser_score = first_id, first_name, first_username, first_score
        winner_id, winner_name, winner_username, winner_score = user_id, name, username, score

    # Записываем в БД
    await record_result(chat_id, winner_id, winner_name, "win")
    await record_result(chat_id, loser_id, loser_name, "loss")

    # Меншен проигравшего
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


@dp.message(F.text == "/stats")
async def cmd_stats(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("Эта команда работает только в группе.")
        return

    row = await get_user_stats(message.chat.id, message.from_user.id)
    if not row:
        await message.answer("Ты ещё не играл. Напиши <b>кубик</b>!")
        return

    name, wins, losses, draws = row
    total = wins + losses + draws

    await message.reply(
        f"📊 <b>Статистика {name}</b>\n\n"
        f"🏆 Побед: {wins}\n"
        f"💀 Поражений: {losses}\n"
        f"🤝 Ничьих: {draws}\n"
        f"🎲 Всего игр: {total}"
    )


@dp.message(F.text == "/topstats")
async def cmd_topstats(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("Эта команда работает только в группе.")
        return

    rows = await get_top_stats(message.chat.id)
    if not rows:
        await message.answer("Пока никто не играл. Напишите <b>кубик</b>!")
        return

    lines = ["🏆 <b>Топ игроков чата</b>\n"]
    for i, (name, wins, losses, draws) in enumerate(rows, 1):
        lines.append(f"{i}. {name} — 🏆{wins} 💀{losses} 🤝{draws}")

    await message.answer("\n".join(lines))


async def main():
    await init_db()
    print("🚀 Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
