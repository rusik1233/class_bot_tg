import telebot
import os
from dotenv import load_dotenv
from gtm_im import model_work
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
TG_API_TOKEN = os.getenv('TG_API_TOKEN')
bot = telebot.TeleBot(TG_API_TOKEN)

# Словарь для хранения последних сообщений пользователей
user_messages = {}

@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    # Создаем клавиатуру
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton('📸 Распознать изображение')
    markup.add(btn1)
    
    text = f'Привет, {message.from_user.username}!\n\n' if message.text == '/start' else ''
    text += 'Отправьте мне фотографию, и я определю породу кошки'
    
    # Сохраняем ID отправленного сообщения
    sent_msg = bot.send_message(message.chat.id, text, reply_markup=markup)
    user_messages[message.chat.id] = sent_msg.message_id

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # Удаляем предыдущее сообщение с клавиатурой
        if message.chat.id in user_messages:
            try:
                bot.delete_message(message.chat.id, user_messages[message.chat.id])
            except:
                pass
        
        # Отправляем сообщение о обработке
        processing_msg = bot.send_message(message.chat.id, "🔄 Обрабатываю изображение...")
        
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        file_bytes = bot.download_file(file_info.file_path)

        image_path = f'user_file/temp_{message.message_id}.jpg'
        os.makedirs('user_file', exist_ok=True)
        
        with open(image_path, 'wb') as f:
            f.write(file_bytes)

        image_class, percentage_probability, error = model_work(image_path)
        
        # Удаляем временный файл
        try:
            os.remove(image_path)
        except:
            pass
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔄 Распознать другое фото", callback_data="new_photo"))
        if error:
            bot.edit_message_text(f"❌ Ошибка: {error}", 
                                message.chat.id, 
                                processing_msg.message_id,
                                reply_markup=keyboard)
            return

        # Создаем инлайн-клавиатуру
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔄 Распознать другое фото", callback_data="new_photo"))
        
        result_text = (f'📊 Результаты распознавания:\n\n'
                      f'🐱 Порода: {image_class}\n'
                      f'📈 Вероятность: {percentage_probability}%')
        
        # Заменяем сообщение о обработке результатом
        bot.edit_message_text(result_text,
                            message.chat.id,
                            processing_msg.message_id,
                            reply_markup=keyboard)
        
    except Exception as e:
        bot.reply_to(message, text=f'❌ Произошла ошибка: {str(e)}')
        

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "new_photo":
        # Удаляем предыдущее сообщение
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # Создаем новую клавиатуру
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('📸 Распознать изображение'))
        
        # Отправляем новое сообщение
        sent_msg = bot.send_message(call.message.chat.id, 
                                  "Отправьте новое фото для распознавания",
                                  reply_markup=markup)
        user_messages[call.message.chat.id] = sent_msg.message_id

# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == '📸 Распознать изображение':
        bot.send_message(message.chat.id, "Отправьте фото для распознавания")
    else:
        bot.send_message(message.chat.id, "Используйте кнопки для взаимодействия")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()