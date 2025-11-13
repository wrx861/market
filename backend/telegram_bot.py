import os
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
WEBAPP_URL = os.environ.get('REACT_APP_WEBAPP_URL', 'https://car-garage-app.preview.emergentagent.com')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    # Создаем клавиатуру с кнопкой для запуска Mini App
    keyboard = [
        [InlineKeyboardButton(
            "🛒 Открыть магазин",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
👋 Привет, {user.first_name}!

Добро пожаловать в магазин автозапчастей! 🚗

🔍 **Что я умею:**
• Поиск запчастей по артикулу
• Поиск по VIN номеру
• AI-поиск запчастей по описанию
• Управление корзиной
• Оформление заказов

Нажмите кнопку ниже, чтобы открыть магазин:
    """
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📚 **Помощь**

**Команды:**
/start - Запустить бота и открыть магазин
/help - Показать эту справку
/shop - Открыть магазин

**Как пользоваться:**

1. **Поиск по артикулу:**
   - Откройте магазин
   - Введите артикул запчасти
   - Получите список доступных предложений

2. **Поиск по VIN:**
   - Введите VIN номер автомобиля
   - Система определит марку и модель
   - Укажите, что вас интересует
   - AI найдет нужную запчасть

3. **Корзина и заказ:**
   - Добавляйте товары в корзину
   - Оформите заказ
   - Мы свяжемся с вами для подтверждения

По вопросам: @support
    """
    
    await update.message.reply_text(help_text)


async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /shop"""
    keyboard = [
        [InlineKeyboardButton(
            "🛒 Открыть магазин",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Нажмите кнопку, чтобы открыть магазин:",
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    # Простая обработка текстовых сообщений
    if len(text) == 17 and text.isalnum():
        # Похоже на VIN номер
        keyboard = [
            [InlineKeyboardButton(
                "🔍 Найти запчасти по VIN",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?vin={text}")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Обнаружен VIN номер: `{text}`\n\n"
            "Нажмите кнопку для поиска запчастей:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        # Обычное сообщение
        keyboard = [
            [InlineKeyboardButton(
                "🛒 Открыть магазин",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Для поиска запчастей откройте магазин:",
            reply_markup=reply_markup
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")


def main():
    """Запуск бота"""
    logger.info("Starting Telegram Bot...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("shop", shop_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
