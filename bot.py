# bot.py
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")  # токен из переменной окружения

# --- Inline-кнопки ---
start_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Старт", callback_data="start")]])
yes_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Да", callback_data="yes")]])
amount_kb = InlineKeyboardMarkup([
    [InlineKeyboardButton("200", callback_data="200")],
    [InlineKeyboardButton("400", callback_data="400")],
    [InlineKeyboardButton("600", callback_data="600")]
])

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo="https://via.placeholder.com/300x150.png?text=Карточка",
        caption="Здравствуйте, это официальный бот для карточек. Чтобы получить карточку, нажмите Старт",
        reply_markup=start_kb
    )

# --- Обработчик всех кнопок ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start":
        await query.message.reply_text(
            "Я разработан компанией сисистик для выдачи карточек. Вы хотите получить карточку сейчас?",
            reply_markup=yes_kb
        )
    elif data == "yes":
        await query.message.reply_text(
            "Хорошо, на какую сумму вы хотите получить карточки?",
            reply_markup=amount_kb
        )
    elif data in ["200", "400", "600"]:
        await query.message.reply_text("Хорошо, сейчас создам пакет карточек специально для тебя")
        loading_msg = await query.message.reply_text("Загрузка: ░░░░░░░░░░")
        for i in range(1, 11):
            await asyncio.sleep(1)
            bar = "█" * i + "░" * (10 - i)
            await loading_msg.edit_text(f"Загрузка: {bar}")
        await query.message.reply_text("Карточка")

# --- Настройка приложения ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("Бот запущен...")
app.run_polling()