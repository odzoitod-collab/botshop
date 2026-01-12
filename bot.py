import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from supabase import create_client, Client

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8333018588:AAHKuqcxw7qYLO_Y2Lzl-3LbjQpAdu3taeo"
BOT_USERNAME = "BlackleafshopBot"
WEBSITE_URL = "https://shop-green-kappa.vercel.app/"
ORDERS_CHANNEL_ID = "-1003488145913"
ADMIN_ID = "844012884"

# Supabase
SUPABASE_URL = "https://owrdpczlmrruxrwuvsow.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93cmRwY3psbXJydXhyd3V2c293Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5NTgyNDMsImV4cCI6MjA4MjUzNDI0M30.l7DYgkTBK_O3AwKqYpCNipz_ajdSlSH1CTSavcIGhBI"
# ======================================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# States для ConversationHandler
(PRODUCT_NAME, PRODUCT_CATEGORY, PRODUCT_DESCRIPTION, 
 PRODUCT_PRICE, PRODUCT_WEIGHT, PRODUCT_IMAGE) = range(6)
(ADMIN_SUPPORT, ADMIN_CARD_NUMBER, ADMIN_CARD_HOLDER, ADMIN_BANK) = range(10, 14)

# Временное хранилище
user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    args = context.args
    
    worker_id = None
    if args and args[0].startswith("ref_"):
        worker_id = args[0].replace("ref_", "")
        
        try:
            existing = supabase.table("mammoths").select("*").eq("user_id", str(user.id)).execute()
            if not existing.data:
                supabase.table("mammoths").insert({
                    "user_id": str(user.id),
                    "username": user.username or "",
                    "first_name": user.first_name or "",
                    "worker_id": worker_id
                }).execute()
                
                # Уведомление воркеру о новом мамонте
                mammoth_name = user.first_name or "Аноним"
                mammoth_username = f"(@{user.username})" if user.username else ""
                
                supabase.table("telegram_notifications").insert({
                    "type": "new_mammoth",
                    "recipient_id": worker_id,
                    "message": f"🦣 НОВЫЙ МАМОНТ!\n\n👤 {mammoth_name} {mammoth_username}\n\nПерешел по твоей реферальной ссылке.",
                    "sent": False
                }).execute()
        except Exception as e:
            print(f"Error saving mammoth: {e}")
    
    welcome_message = """
🌿 *Приветствую тебя!*

Лучшие товары только у нас! 
📍 Все города России

Нажми кнопку ниже, чтобы открыть наш магазин 👇
"""
    
    webapp_url = f"{WEBSITE_URL}?worker={worker_id}" if worker_id else WEBSITE_URL
    
    # Получаем ник поддержки из базы
    try:
        support_result = supabase.table("settings").select("value").eq("key", "telegram_support").single().execute()
        support_username = support_result.data.get("value", "@support") if support_result.data else "@support"
    except:
        support_username = "@support"
    
    support_link = f"https://t.me/{support_username.replace('@', '')}"
    
    keyboard = [
        [InlineKeyboardButton(text="🛒 Открыть магазин", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton(text="📞 Тех. поддержка", url=support_link)]
    ]
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Воркер панель"""
    user = update.effective_user
    worker_id = str(user.id)
    
    try:
        existing = supabase.table("workers").select("*").eq("user_id", worker_id).execute()
        if not existing.data:
            supabase.table("workers").insert({
                "user_id": worker_id,
                "username": user.username or "",
                "first_name": user.first_name or ""
            }).execute()
    except Exception as e:
        print(f"Error registering worker: {e}")
    
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{worker_id}"
    
    message = f"""
👷 *Воркер панель*

🔗 Твоя реферальная ссылка:
`{ref_link}`

Отправляй эту ссылку клиентам.
"""
    
    keyboard = [
        [InlineKeyboardButton("🦣 Мои мамонты", callback_data="my_mammoths")],
        [InlineKeyboardButton("📦 Мои товары", callback_data="my_products")],
        [InlineKeyboardButton("➕ Добавить товар", callback_data="start_add_product")]
    ]
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def worker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок воркера"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    worker_id = str(user.id)
    
    if query.data == "my_mammoths":
        try:
            result = supabase.table("mammoths").select("*").eq("worker_id", worker_id).execute()
            mammoths = result.data
            
            if not mammoths:
                message = "🦣 *Мои мамонты*\n\nУ тебя пока нет мамонтов."
            else:
                message = f"🦣 *Мои мамонты* ({len(mammoths)})\n\n"
                for i, m in enumerate(mammoths, 1):
                    username = f"@{m['username']}" if m.get('username') else "без username"
                    message += f"{i}. {m.get('first_name', 'Аноним')} ({username})\n"
        except Exception as e:
            message = f"Ошибка: {e}"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_worker")]]
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "my_products":
        try:
            result = supabase.table("worker_products").select("*").eq("worker_id", worker_id).execute()
            products = result.data
            
            if not products:
                message = "📦 *Мои товары*\n\nУ тебя пока нет товаров."
                keyboard = [
                    [InlineKeyboardButton("➕ Добавить товар", callback_data="start_add_product")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_worker")]
                ]
            else:
                message = f"📦 *Мои товары* ({len(products)})\n\n"
                keyboard = []
                for p in products:
                    message += f"• {p['name']} — {p['price']}₽ ({p['weight']})\n"
                    keyboard.append([InlineKeyboardButton(f"🗑 {p['name']}", callback_data=f"del_{p['id']}")])
                keyboard.append([InlineKeyboardButton("➕ Добавить", callback_data="start_add_product")])
                keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_worker")])
        except Exception as e:
            message = f"Ошибка: {e}"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_worker")]]
        
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "back_to_worker":
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{worker_id}"
        message = f"👷 *Воркер панель*\n\n🔗 Ссылка:\n`{ref_link}`"
        keyboard = [
            [InlineKeyboardButton("🦣 Мои мамонты", callback_data="my_mammoths")],
            [InlineKeyboardButton("📦 Мои товары", callback_data="my_products")],
            [InlineKeyboardButton("➕ Добавить товар", callback_data="start_add_product")]
        ]
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith("del_"):
        product_id = query.data.replace("del_", "")
        try:
            supabase.table("worker_products").delete().eq("id", product_id).eq("worker_id", worker_id).execute()
            await query.answer("✅ Удалено!")
            # Обновляем список
            result = supabase.table("worker_products").select("*").eq("worker_id", worker_id).execute()
            products = result.data
            message = f"📦 *Мои товары* ({len(products)})\n\n" if products else "📦 *Мои товары*\n\nПусто."
            keyboard = []
            for p in products:
                message += f"• {p['name']} — {p['price']}₽\n"
                keyboard.append([InlineKeyboardButton(f"🗑 {p['name']}", callback_data=f"del_{p['id']}")])
            keyboard.append([InlineKeyboardButton("➕ Добавить", callback_data="start_add_product")])
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_worker")])
            await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.answer(f"Ошибка: {e}")


# ==================== ДОБАВЛЕНИЕ ТОВАРА ====================

async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления товара"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data[user_id] = {"action": "add_product"}
    
    await query.edit_message_text(
        "📦 *Добавление товара*\n\nВведи название товара:",
        parse_mode="Markdown"
    )
    return PRODUCT_NAME


async def product_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название"""
    user_id = str(update.effective_user.id)
    user_data[user_id]["name"] = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("🌿 Трава", callback_data="pcat_Трава")],
        [InlineKeyboardButton("💊 MDMA", callback_data="pcat_MDMA")],
        [InlineKeyboardButton("🎨 LSD", callback_data="pcat_LSD")],
        [InlineKeyboardButton("🔧 Аксессуары", callback_data="pcat_Аксессуары")]
    ]
    
    await update.message.reply_text("Выбери категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    return PRODUCT_CATEGORY


async def product_get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить категорию"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data[user_id]["category"] = query.data.replace("pcat_", "")
    
    await query.edit_message_text("Введи описание товара:")
    return PRODUCT_DESCRIPTION


async def product_get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить описание"""
    user_id = str(update.effective_user.id)
    user_data[user_id]["description"] = update.message.text
    
    await update.message.reply_text("Введи цену (число):")
    return PRODUCT_PRICE


async def product_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить цену"""
    user_id = str(update.effective_user.id)
    
    try:
        user_data[user_id]["price"] = int(update.message.text)
        await update.message.reply_text("Введи вес/объем (например: 1г):")
        return PRODUCT_WEIGHT
    except ValueError:
        await update.message.reply_text("❌ Введи число!")
        return PRODUCT_PRICE


async def product_get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить вес"""
    user_id = str(update.effective_user.id)
    user_data[user_id]["weight"] = update.message.text
    
    await update.message.reply_text("Отправь ссылку на изображение (URL):")
    return PRODUCT_IMAGE


async def product_get_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить URL изображения и сохранить товар"""
    user_id = str(update.effective_user.id)
    
    # Получаем только URL (не принимаем фото)
    image_url = update.message.text.strip()
    
    # Проверяем что это URL
    if not (image_url.startswith('http://') or image_url.startswith('https://')):
        await update.message.reply_text("❌ Введи правильную ссылку на изображение (начинается с http)")
        return PRODUCT_IMAGE
    
    user_data[user_id]["image"] = image_url
    
    try:
        data = user_data[user_id]
        result = supabase.table("worker_products").insert({
            "worker_id": user_id,
            "name": data["name"],
            "category": data["category"],
            "description": data["description"],
            "price": data["price"],
            "weight": data["weight"],
            "image": data["image"]
        }).execute()
        
        print(f"✅ Product added for worker {user_id}: {data['name']}")
        
        await update.message.reply_text(
            f"✅ Товар добавлен!\n\n📦 {data['name']}\n💰 {data['price']}₽\n📏 {data['weight']}\n\nТовар появится на сайте для твоих мамонтов."
        )
        del user_data[user_id]
    except Exception as e:
        print(f"❌ Error adding product: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    user_id = str(update.effective_user.id)
    if user_id in user_data:
        del user_data[user_id]
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END


# ==================== АДМИН ПАНЕЛЬ ====================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ панель"""
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("⛔ Нет доступа.")
        return
    
    try:
        support_result = supabase.table("settings").select("value").eq("key", "telegram_support").single().execute()
        support = support_result.data.get("value", "@support") if support_result.data else "@support"
        
        payment_result = supabase.table("payment_details").select("*").eq("is_active", True).limit(1).single().execute()
        payment = payment_result.data
    except:
        support = "@support"
        payment = None
    
    card_info = f"{payment['card_number']} ({payment['bank_name']})" if payment else "Не установлены"
    
    message = f"👑 *Админ панель*\n\n📞 Поддержка: `{support}`\n💳 Реквизиты: {card_info}"
    
    keyboard = [
        [InlineKeyboardButton("📞 Изменить поддержку", callback_data="adm_support")],
        [InlineKeyboardButton("💳 Изменить реквизиты", callback_data="adm_payment")],
        [InlineKeyboardButton("📊 Статистика", callback_data="adm_stats")]
    ]
    
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик админ кнопок"""
    query = update.callback_query
    await query.answer()
    
    if str(query.from_user.id) != ADMIN_ID:
        return
    
    if query.data == "adm_stats":
        try:
            workers = supabase.table("workers").select("*", count="exact").execute()
            mammoths = supabase.table("mammoths").select("*", count="exact").execute()
            orders = supabase.table("orders").select("total").execute()
            total_sum = sum(o.get("total", 0) for o in orders.data) if orders.data else 0
            
            message = f"📊 *Статистика*\n\n👷 Воркеров: {workers.count or 0}\n🦣 Мамонтов: {mammoths.count or 0}\n🛒 Заказов: {len(orders.data)}\n💰 Сумма: {total_sum}₽"
        except Exception as e:
            message = f"Ошибка: {e}"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="adm_back")]]
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "adm_back":
        await query.edit_message_text("👑 *Админ панель*\n\nВыберите действие:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Поддержка", callback_data="adm_support")],
            [InlineKeyboardButton("💳 Реквизиты", callback_data="adm_payment")],
            [InlineKeyboardButton("📊 Статистика", callback_data="adm_stats")]
        ]))


async def admin_start_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать изменение поддержки"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if user_id != ADMIN_ID:
        return ConversationHandler.END
    
    user_data[user_id] = {"action": "admin_support"}
    await query.edit_message_text("📞 Введите новый username поддержки (например @support):")
    return ADMIN_SUPPORT


async def admin_get_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранить поддержку"""
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return ConversationHandler.END
    
    new_support = update.message.text.strip()
    
    try:
        existing = supabase.table("settings").select("*").eq("key", "telegram_support").execute()
        if existing.data:
            supabase.table("settings").update({"value": new_support}).eq("key", "telegram_support").execute()
        else:
            supabase.table("settings").insert({"key": "telegram_support", "value": new_support}).execute()
        
        await update.message.reply_text(f"✅ Поддержка изменена на: {new_support}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END


async def admin_start_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать изменение реквизитов"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if user_id != ADMIN_ID:
        return ConversationHandler.END
    
    user_data[user_id] = {"action": "admin_payment"}
    await query.edit_message_text("� Введите номер карты:")
    return ADMIN_CARD_NUMBER


async def admin_get_card_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data[user_id]["card_number"] = update.message.text.strip()
    await update.message.reply_text("Введите имя держателя (латиницей):")
    return ADMIN_CARD_HOLDER


async def admin_get_card_holder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data[user_id]["card_holder"] = update.message.text.strip().upper()
    await update.message.reply_text("Введите название банка:")
    return ADMIN_BANK


async def admin_get_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data[user_id]["bank_name"] = update.message.text.strip()
    
    try:
        supabase.table("payment_details").update({"is_active": False}).eq("is_active", True).execute()
        supabase.table("payment_details").insert({
            "card_number": user_data[user_id]["card_number"],
            "card_holder": user_data[user_id]["card_holder"],
            "bank_name": user_data[user_id]["bank_name"],
            "is_active": True
        }).execute()
        
        await update.message.reply_text(f"✅ Реквизиты обновлены!\n\n💳 {user_data[user_id]['card_number']}\n👤 {user_data[user_id]['card_holder']}\n🏦 {user_data[user_id]['bank_name']}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")
    
    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END


# ==================== УВЕДОМЛЕНИЯ ====================

async def check_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Проверка и отправка уведомлений"""
    try:
        result = supabase.table("telegram_notifications").select("*").eq("sent", False).execute()
        
        for n in result.data:
            try:
                n_type = n.get("type")
                recipient = n.get("recipient_id")
                screenshot = n.get("screenshot_url")
                message = n.get("message", "")
                
                # Убираем проблемные символы Markdown
                message = message.replace("*", "").replace("_", "").replace("`", "")
                
                # Определяем куда отправлять
                if n_type == "new_order" and recipient == "channel":
                    chat_id = ORDERS_CHANNEL_ID
                elif n_type == "worker_order" and recipient:
                    chat_id = recipient
                elif n_type == "new_mammoth" and recipient:
                    chat_id = recipient
                else:
                    print(f"Unknown notification type: {n_type}, recipient: {recipient}")
                    continue
                
                # Отправляем со скриншотом если есть
                if screenshot:
                    try:
                        await context.bot.send_photo(chat_id=chat_id, photo=screenshot, caption=message)
                    except Exception as photo_err:
                        print(f"Photo send error: {photo_err}")
                        await context.bot.send_message(chat_id=chat_id, text=f"{message}\n\nСкриншот: {screenshot}")
                else:
                    await context.bot.send_message(chat_id=chat_id, text=message)
                
                supabase.table("telegram_notifications").update({"sent": True}).eq("id", n["id"]).execute()
                print(f"✅ Sent notification to {chat_id}")
            except Exception as e:
                print(f"❌ Notification error for {n.get('id')}: {e}")
                # Помечаем как отправленное чтобы не спамить ошибками
                supabase.table("telegram_notifications").update({"sent": True}).eq("id", n["id"]).execute()
                
    except Exception as e:
        print(f"Check notifications error: {e}")


def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ConversationHandler для добавления товара
    product_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_product, pattern="^start_add_product$")],
        states={
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_get_name)],
            PRODUCT_CATEGORY: [CallbackQueryHandler(product_get_category, pattern="^pcat_")],
            PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_get_description)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_get_price)],
            PRODUCT_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_get_weight)],
            PRODUCT_IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_get_image)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    
    # ConversationHandler для админ поддержки
    admin_support_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_start_support, pattern="^adm_support$")],
        states={
            ADMIN_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_support)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    
    # ConversationHandler для админ реквизитов
    admin_payment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_start_payment, pattern="^adm_payment$")],
        states={
            ADMIN_CARD_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_card_number)],
            ADMIN_CARD_HOLDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_card_holder)],
            ADMIN_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_get_bank)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    
    # Регистрация handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("worker", worker))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(product_conv)
    app.add_handler(admin_support_conv)
    app.add_handler(admin_payment_conv)
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"))
    app.add_handler(CallbackQueryHandler(worker_callback))
    
    # Проверка уведомлений каждые 10 сек
    app.job_queue.run_repeating(check_notifications, interval=10, first=5)
    
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
