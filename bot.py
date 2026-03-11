import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")

# Inline-кнопка "Старт"
start_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Старт", callback_data="start")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_photo(
        photo="https://via.placeholder.com/300x150.png?text=Карточка",  # сюда можно вставить свою картинку
        caption="Здравствуйте, это официальный бот для карточек. Чтобы получить карточку, нажмите Старт",
        reply_markup=start_kb
    )

# Пока не обрабатываем нажатия кнопки
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("Бот запущен...")
app.run_polling()