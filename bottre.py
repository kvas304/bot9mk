import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
TOKEN = 'TOKEN'
TRENER_ID = 'id'  

# Создаем экземпляр бота
bot = telebot.TeleBot(TOKEN)

# Хранение данных пользователей
user_data = {}

# Состояния
STATE_NAME, STATE_SURNAME, STATE_PHONE = range(3)

@bot.message_handler(commands=['start'])
def start(message):
    """Обработка команды /start"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Хочу на тренировку", callback_data='start_training'))
    bot.send_message(message.chat.id, 'Добро пожаловать! Нажмите кнопку ниже, чтобы начать:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'start_training')
def start_training(call):
    """Начало процесса записи на тренировку"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Каратэ", callback_data='karate'))
    markup.add(InlineKeyboardButton("Капоэйра для детей", callback_data='kapoeyra_for_kids'))
    markup.add(InlineKeyboardButton("Нейрофитнес для детей", callback_data='neyrofitness_for_kids'))
    markup.add(InlineKeyboardButton("Тхэквондо", callback_data='txekvondo'))
    markup.add(InlineKeyboardButton("Кобудо", callback_data='kobudo'))
    markup.add(InlineKeyboardButton("Ниндзя-клуб", callback_data='nindza-club'))
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Выберите вид тренировки:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ['karate', 'kapoeyra_for_kids', 'neyrofitness_for_kids', 'txekvondo', 'kobudo', 'nindza-club'])
def select_sport(call):
    """Обработка выбора вида спорта"""
    user_data[call.from_user.id] = {
        'sport': call.data,
        'username': f"@{call.from_user.username}" if call.from_user.username else "Не указан"
    }
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Пожалуйста, напишите ваше имя:"
    )
    bot.register_next_step_handler(call.message, get_name)

def get_name(message):
    """Получение имени"""
    user_id = message.from_user.id
    user_data[user_id]['name'] = message.text
    bot.send_message(message.chat.id, "Теперь напишите вашу фамилию:")
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    """Получение фамилии"""
    user_id = message.from_user.id
    user_data[user_id]['surname'] = message.text
    
    # Создаем кнопку для отправки контакта
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📱 Поделиться номером", request_contact=True))
    
    bot.send_message(
        message.chat.id,
        "Пожалуйста, поделитесь вашим номером телефона для связи:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    """Получение номера телефона и показ дней"""
    user_id = message.from_user.id
    
    # Получаем номер телефона
    if message.contact:
        user_data[user_id]['phone'] = message.contact.phone_number
    else:
        user_data[user_id]['phone'] = message.text
    
    # Убираем клавиатуру с кнопкой телефона
    markup = ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id,
        "Спасибо! Теперь выберите удобный день:",
        reply_markup=markup
    )
    
    # Кнопки для выбора дня
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Понедельник", callback_data='Понедельник'),
        InlineKeyboardButton("Вторник", callback_data='Вторник')
    )
    markup.row(
        InlineKeyboardButton("Среда", callback_data='Среда'),
        InlineKeyboardButton("Четверг", callback_data='Четверг')
    )
    markup.add(InlineKeyboardButton("Пятница", callback_data='Пятница'))
    
    bot.send_message(
        message.chat.id,
        "Выберите день недели для тренировки:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'])
def select_day(call):
    """Обработка выбора дня и отправка заявки"""
    user_id = call.from_user.id
    day = call.data
    user_data[user_id]['day'] = day
    
    # Формируем текст заявки
    user = user_data[user_id]
    application_text = (
        "🏆 Новая заявка на тренировку 🏆\n"
        f"👤 Имя: {user.get('name', '')} {user.get('surname', '')}\n"
        f"📞 Телефон: {user.get('phone', 'Не указан')}\n"
        f"📌 Тренировка: {user.get('sport', '')}\n"
        f"📅 День: {day}\n"
        f"🔗 Telegram: {user.get('username', '')}\n"
        f"🆔 ID: {user_id}"
    )
    
    # Отправляем пользователю
    bot.send_message(call.message.chat.id, f"✅ Ваша заявка принята!\n\n{application_text}")
    
    # Отправляем тренеру
    try:
        bot.send_message(TRENER_ID, f"📬 НОВАЯ ЗАЯВКА!\n\n{application_text}")
    except Exception as e:
        logger.error(f"Ошибка отправки тренеру: {e}")
        bot.send_message(
            call.message.chat.id,
            "⚠️ Произошла ошибка при отправке заявки тренеру. Пожалуйста, сообщите об этом администратору."
        )
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="✅ Регистрация завершена! Тренер свяжется с вами."
    )

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Обработка прочих сообщений"""
    bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки меню или команду /start")

if __name__ == '__main__':
    logger.info("Бот запущен")
    bot.polling(none_stop=True)
