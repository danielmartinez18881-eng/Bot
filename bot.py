import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")

# Inline-кнопка "Старт"
start_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Старт", callback_data="start")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Путь к локальному файлу
    photo_path = os.path.join("images", "card.jpg")
    
    with open(photo_path, "rb") as photo_file:
        await update.message.reply_photo(
            photo=photo_file,
            caption="Здравствуйте, это официальный бот для карточек. Чтобы получить карточку, нажмите Старт",
            reply_markup=start_kb
        )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("Бот запущен...")
app.run_polling()