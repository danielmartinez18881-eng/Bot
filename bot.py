import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TOKEN")

# --- Inline-клавиатуры ---
start_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Старт", callback_data="start")]])
yes_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Да", callback_data="yes")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = os.path.join("images", "card.jpg")
    with open(photo_path, "rb") as photo_file:
        await update.message.reply_photo(
            photo=photo_file,
            caption="Здравствуйте, это официальный бот для карточек. Чтобы получить карточку, нажмите Старт",
            reply_markup=start_kb
        )

# --- Обработчик нажатий кнопок ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # подтверждаем нажатие
    data = query.data

    if data == "start":
        # При нажатии на "Старт" показываем сообщение и кнопку "Да"
        await query.message.reply_text(
            "Я разработан компанией сисистик для выдачи карточек. Вы хотите получить карточку сейчас?",
            reply_markup=yes_kb
        )
    elif data == "yes":
        # Пока оставим пустым — это будет следующий этап
        await query.message.reply_text("Вы нажали Да — здесь будет выбор суммы")

# --- Настройка приложения ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

print("Бот запущен...")
app.run_polling()