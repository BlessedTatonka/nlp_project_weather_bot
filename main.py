# !pip3 install pyTelegramBotAPI
# !pip3 install transformers
# !python -m spacy download ru_core_news_lg
# !pip install autocorrect
# !pip install deep_translator

import os

import telebot
from src.bot import BotState
from modules.ydisk_photo_module import add_photo_to_disk


class BotConfig:
    API_KEY = os.getenv('TELEGRAM_API_TOKEN')
    USERNAME = 'https://t.me/weather_forecast_nlp_project_bot'

bot = telebot.TeleBot(BotConfig.API_KEY)
bot_state = BotState()


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, 'Some help')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    response, responce_type = None, 'message'
    try:
        response, responce_type = bot_state.process(message.from_user.id, message.text)
    except Exception as e:
        response = f'Возникла ошибка: {e}'

    if response is not None:
        if responce_type == 'message':
            bot.reply_to(message, response)
        elif responce_type == 'photo':
            bot.send_photo(message.chat.id, response)


@bot.message_handler(content_types=['photo'])
def add_photo(message):
    try:
        text = message.caption
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        response = add_photo_to_disk(text, downloaded_file)
        bot.reply_to(message, response)
    except:
        pass

print('Bot polling is set up')
bot.polling(none_stop=True, interval=1)