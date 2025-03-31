from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from datetime import datetime
import os
from flask import Flask, request

# Словарь для хранения запросов на выходной (аналог базы данных)
requests = {}

# Установим последовательность смен
shifts = ["Ночь", "Утро", "День"]

# Функция для обработки запроса на выходной
async def request_off_day(update: Update, context):
    user = update.message.from_user
    request = update.message.text.strip().split("\n")
    
    # Проверка формата запроса
    if len(request) != 3:
        await update.message.reply_text("Пожалуйста, укажите запрос в формате: \n1. Имя анкеты\n2. Дата\n3. Смена")
        return
    
    # Извлекаем данные из запроса
    name = request[0].strip().split(". ")[1]
    date = request[1].strip().split(". ")[1]
    shift = request[2].strip().split(". ")[1]
    
    # Проверка правильности смены
    if shift not in shifts:
        await update.message.reply_text("Неверная смена. Укажите одну из следующих: Ночь, Утро, День.")
        return
    
    # Проверка формата даты (ДД.ММ)
    try:
        datetime.strptime(date, "%d.%m")
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Пожалуйста, используйте формат: 'День.Месяц'.")
        return
    
    # Проверка, был ли уже принят выходной в этот день
    if date not in requests:
        requests[date] = {}

    # Если для анкеты уже есть выходной в этот день, не даем выходной на другие смены этой анкеты
    if name in requests[date]:
        await update.message.reply_text(f"На {date} для анкеты {name} уже был принят выходной. Не могу предоставить другой выходной в этот день.")
        return
    
    # Проверка, если для этого дня уже был принят выходной на эту смену
    if shift in [user_shift for user_requests in requests.values() for user_shift in user_requests.values()]:
        await update.message.reply_text(f"На {date} смена {shift} уже занята. Пожалуйста, выберите другую смену.")
        return

    # Если запрос принят, добавляем его в список для этой даты
    if date not in requests:
        requests[date] = {}

    requests[date][name] = shift

    await update.message.reply_text(f"Запрос на выходной принят: {name}, {date}, {shift}")
    
    # Проверка на доступность только оставшихся смен
    available_shifts = [s for s in shifts if s not in [user_shift for user_requests in requests.values() for user_shift in user_requests.values()]]

    # Если нет доступных смен, уведомляем пользователя
    if not available_shifts:
        await update.message.reply_text(f"На {date} все смены заняты. Вы можете выбрать другой день.")
    else:
        await update.message.reply_text(f"Для {date} доступны следующие свободные смены: {', '.join(available_shifts)}")

# Функция для очистки базы данных
async def clear_data(update: Update, context):
    # Проверка, является ли пользователь администратором
    admin_user_ids = [7728175615]  # Здесь указываем ID администраторов бота
    user_id = update.message.from_user.id
    
    if user_id not in admin_user_ids:
        await update.message.reply_text("У вас нет прав для очистки базы данных.")
        return
    
    # Очистка базы данных
    global requests
    requests = {}
    await update.message.reply_text("База данных очищена.")

# Основная функция для запуска бота с вебхуком
def main():
    application = Application.builder().token('7689018373:AAEdAM6-hsXFzkhhc_XdrrLTlkoN7D8OAUE').build()

    # Обработчик для команд
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, request_off_day))
    application.add_handler(CommandHandler("clear", clear_data))  # Обработчик для команды очистки данных

    # Flask приложение
    app = Flask(__name__)

    @app.route('/')
    def index():
        return "Bot is running!"

    @app.route('/webhook', methods=['POST'])
    def webhook():
        json_str = request.get_data(as_text=True)
        update = Update.de_json(json_str, application.bot)
        application.process_update(update)
        return '', 200

    # Установка webhook
    webhook_url = f"https://radiant-shelf-10274.herokuapp.com/webhook"
    application.bot.set_webhook(url=webhook_url)
    
    # Запуск приложения через Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    main()