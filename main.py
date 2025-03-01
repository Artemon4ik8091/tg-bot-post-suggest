import telebot
import json

with open('config.json', 'r') as f:
    config = json.load(f)

BOT_TOKEN = config['bot_token']
ADMIN_USER_IDS = config['admin_user_ids']
CHANNEL_ID = config['channel_id']

bot = telebot.TeleBot(BOT_TOKEN)

proposals = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Отправьте ваше предложение (текст или изображение), и оно будет отправлено администраторам на рассмотрение.")

@bot.message_handler(content_types=['text', 'photo', 'caption'])
def handle_proposal(message):
    if message.from_user.id in ADMIN_USER_IDS:
        return

    proposal = {'user_id': message.from_user.id}

    if message.text:
        proposal['text'] = message.text
    elif message.photo:
        proposal['photo'] = message.photo[-1].file_id
        if message.caption:
            proposal['caption'] = message.caption

    proposals[message.message_id] = proposal

    for admin_id in ADMIN_USER_IDS:
        keyboard = telebot.types.InlineKeyboardMarkup()
        approve_button = telebot.types.InlineKeyboardButton(text="Одобрить", callback_data=f"approve_{message.message_id}")
        reject_button = telebot.types.InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{message.message_id}")
        keyboard.add(approve_button, reject_button)

        if 'text' in proposal:
            bot.send_message(admin_id, f"Новое предложение:\n\n{proposal['text']}", reply_markup=keyboard)
        elif 'photo' in proposal:
            if 'caption' in proposal:
                bot.send_photo(admin_id, proposal['photo'], caption=f"Новое предложение (изображение):\n\n{proposal['caption']}", reply_markup=keyboard)
            else:
                bot.send_photo(admin_id, proposal['photo'], caption="Новое предложение (изображение)", reply_markup=keyboard)

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
    proposal = proposals[message_id]

    if action == 'approve':
        if 'text' in proposal:
            bot.send_message(user_id, f"Предложение было одобрено.")
            bot.send_message(CHANNEL_ID, f"Одобренное предложение:\n\n{proposal['text']}") # Отправляем в канал
            for admin_id in ADMIN_USER_IDS:
                bot.send_message(admin_id, f"Предложение одобрено")
        elif 'photo' in proposal:
            if 'caption' in proposal:
                bot.send_message(user_id, f"Предложение было одобрено.")
                bot.send_photo(CHANNEL_ID, proposal['photo'], caption=f"Одобренное предложение (изображение):\n\n{proposal['caption']}") # Отправляем в канал
                for admin_id in ADMIN_USER_IDS:
                    bot.send_message(admin_id, f"Предложение (изображение) одобрено.")
            else:
                bot.send_message(user_id, f"Предложение было одобрено.")
                bot.send_photo(CHANNEL_ID, proposal['photo'], caption=f"Одобренное предложение (изображение):\n\n{proposal['caption']}") # Отправляем в канал
                for admin_id in ADMIN_USER_IDS:
                    bot.send_message(admin_id, f"Предложение (изображение) одобрено.")
        
    else:
        if 'text' in proposal:
            bot.send_message(user_id, f"Ваше предложение было отклонено")
            for admin_id in ADMIN_USER_IDS:
                bot.send_message(admin_id, f"Предложение отклонено.")
        elif 'photo' in proposal:
            bot.send_message(user_id, "Ваше предложение (изображение) было отклонено.")
            for admin_id in ADMIN_USER_IDS:
                bot.send_message(admin_id, f"Предложение (изображение) отклонено.")

    del proposals[message_id]

bot.polling()
