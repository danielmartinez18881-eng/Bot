import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

# --- клавиатуры ---
start_kb = ReplyKeyboardMarkup([["Старт"]], one_time_keyboard=True, resize_keyboard=True)
yes_kb = ReplyKeyboardMarkup([["Да"]], one_time_keyboard=True, resize_keyboard=True)
amount_kb = ReplyKeyboardMarkup([["200", "400", "600"]], one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = os.path.join("images", "card.jpg")
    with open(photo_path, "rb") as photo_file:
        await update.message.reply_photo(
            photo=photo_file,
            caption="Здравствуйте, это официальный бот для карточек. Чтобы получить карточку, нажмите Старт",
            reply_markup=start_kb
        )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Старт":
        await update.message.reply_text(
            "Я разработан компанией сисистик для выдачи карточек. Вы хотите получить карточку сейчас?",
            reply_markup=yes_kb
        )
    elif text == "Да":
        await update.message.reply_text(
            "Хорошо, на какую сумму вы хотите получить карточки?",
            reply_markup=amount_kb
        )
    elif text in ["200", "400", "600"]:
        await update.message.reply_text(f"Хорошо, сейчас создам пакет карточек специально для тебя ({text})")

        # Анимация загрузки 10 секунд
        loading_msg = await update.message.reply_text("Загрузка: ░░░░░░░░░░")
        for i in range(1, 11):
            await asyncio.sleep(1)
            bar = "█" * i + "░" * (10 - i)
            await loading_msg.edit_text(f"Загрузка: {bar}")

        # Финальная карточка (текст)
        await update.message.reply_text("Карточка")
    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки ниже для выбора.")

# --- Настройка приложения ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("Бот запущен...")
app.run_polling()