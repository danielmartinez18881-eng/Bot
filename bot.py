import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Не установлен токен бота в переменной окружения TOKEN")

# --- функции для клавиатур ---
def make_keyboard(options):
    return ReplyKeyboardMarkup([options], one_time_keyboard=True, resize_keyboard=True)

start_kb = make_keyboard(["Старт"])
yes_kb = make_keyboard(["Да"])
amount_kb = make_keyboard(["200", "400", "600"])

# --- стартовое сообщение ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = os.path.join("images", "card.jpg")
    if os.path.exists(photo_path):
        with open(photo_path, "rb") as photo_file:
            await update.message.reply_photo(
                photo=photo_file,
                caption="Здравствуйте, это официальный бот для карточек. Чтобы получить карточку, нажмите Старт",
                reply_markup=start_kb
            )
    else:
        await update.message.reply_text(
            "Здравствуйте, это официальный бот для карточек. Чтобы получить карточку, нажмите Старт",
            reply_markup=start_kb
        )

# --- функция для анимации и выдачи карточки ---
async def send_cards(update, amount):
    await update.message.reply_text(f"Генерируем пакет карточек ({amount})")
    
    # Создаём сообщение загрузки
    total_seconds = 14
    loading_msg = await update.message.reply_text("Загрузка: " + "░" * total_seconds)
    
    # Анимация загрузки
    for i in range(1, total_seconds + 1):
        await asyncio.sleep(1)
        bar = "█" * i + "░" * (total_seconds - i)
        await loading_msg.edit_text(f"Загрузка: {bar}")
    
    # Загрузка завершена — заменяем сообщение на "Карточка"
    await loading_msg.edit_text("Карточка")

# --- обработчик текстовых сообщений ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    state = context.user_data.get("state", "START")

    if state == "START" and text == "Старт":
        await update.message.reply_text(
            "Я разработан компанией сисистик для выдачи карточек. Вы хотите получить карточку сейчас?",
            reply_markup=yes_kb
        )
        context.user_data["state"] = "ASK_YES"

    elif state == "ASK_YES" and text == "Да":
        await update.message.reply_text(
            "Хорошо, на какую сумму вы хотите получить карточки?",
            reply_markup=amount_kb
        )
        context.user_data["state"] = "ASK_AMOUNT"

    elif state == "ASK_AMOUNT" and text in ["200", "400", "600"]:
        await send_cards(update, text)
        context.user_data["state"] = "START"

    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки ниже для выбора.")

# --- настройка приложения ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("Бот запущен...")
app.run_polling()