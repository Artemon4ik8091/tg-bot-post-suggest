import telebot
import json

# Загружаем конфигурацию из JSON-файла
with open('config.json', 'r') as f:
    config = json.load(f)

BOT_TOKEN = config['bot_token']
ADMIN_USER_IDS = config['admin_user_ids']

bot = telebot.TeleBot(BOT_TOKEN)

proposals = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Отправьте ваше предложение, и оно будет отправлено администраторам на рассмотрение.")

@bot.message_handler(func=lambda message: True)
def handle_proposal(message):
    if message.from_user.id in ADMIN_USER_IDS:
        return

    proposals[message.message_id] = {'user_id': message.from_user.id, 'text': message.text}

    for admin_id in ADMIN_USER_IDS:
        keyboard = telebot.types.InlineKeyboardMarkup()
        approve_button = telebot.types.InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{message.message_id}")
        reject_button = telebot.types.InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{message.message_id}")
        keyboard.add(approve_button, reject_button)
        bot.send_message(admin_id, f"Новое предложение:\n\n{message.text}", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def handle_approval(call):
    message_id = int(call.data.split('_')[1])
    action = call.data.split('_')[0]

    if call.from_user.id not in ADMIN_USER_IDS:
        return

    if message_id not in proposals:
        bot.answer_callback_query(call.id, "Предложение уже было обработано.")
        return

    user_id = proposals[message_id]['user_id']
    text = proposals[message_id]['text']

    if action == 'approve':
        bot.send_message(user_id, f"Ваше предложение было одобрено:\n\n{text}")
        for admin_id in ADMIN_USER_IDS:
            bot.send_message(admin_id, f"Предложение одобрено:\n\n{text}")
    else:
        bot.send_message(user_id, f"Ваше предложение было отклонено:\n\n{text}")
        for admin_id in ADMIN_USER_IDS:
            bot.send_message(admin_id, f"Предложение отклонено:\n\n{text}")

    del proposals[message_id]

bot.polling()