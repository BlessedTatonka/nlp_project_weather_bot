# !pip3 install pyTelegramBotAPI
# !pip3 install transformers
# !python -m spacy download ru_core_news_lg
# !pip install autocorrect
# !pip install deep_translator

import os

import telebot
from src.bot import BotState
from modules.ydisk_photo_module import add_photo_to_disk
from telebot import types
from datetime import datetime
import src.database_processor as db

os.environ['WEATHER_API_TOKEN'] = '7Z2PR8YDYTFJALLMMT7BJVLDX'
os.environ['YDISK_API_TOKEN'] = 'OAuth y0_AgAEA7qkJR7kAADLWwAAAADUET6Z7XHjJotrSjqOLnilwyq5bx4MfIA'
os.environ['TELEGRAM_API_TOKEN'] = '5914874422:AAE-AlgM71e_N7S4mZMxYMMYVK7770iwH8M'


class BotConfig:
    API_KEY = os.getenv('TELEGRAM_API_TOKEN')
    USERNAME = 'https://t.me/weather_forecast_nlp_project_bot'
    TEST_MODE = True
    CREATOR_ID = 426892637

    
bot = telebot.TeleBot(BotConfig.API_KEY)
bot_state = BotState()

@bot.message_handler(commands=['help'])
def send_help(message):
    with open('data/help.txt', 'r') as fin:
        bot.reply_to(message, fin.read())


def get_keyboard():
    # keyboard = types.InlineKeyboardMarkup()
    # keyboard.row(types.InlineKeyboardButton(sign, callback_data=cd) for sign, cd in buttons)
    # return keyboard
    
    button_yes = types.InlineKeyboardButton('✅', callback_data='cb_yes')
    button_no = types.InlineKeyboardButton('❌', callback_data='cb_no')
    button_fv = types.InlineKeyboardButton('⭐', callback_data='cb_fv')
    button_re = types.InlineKeyboardButton('🔄', callback_data='cb_re')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(button_yes, button_no, button_fv, button_re)
    
    return keyboard
    
def get_keyboard_no_fav():
    button_yes = types.InlineKeyboardButton('✅', callback_data='cb_yes')
    button_no = types.InlineKeyboardButton('❌', callback_data='cb_no')
    button_re = types.InlineKeyboardButton('🔄', callback_data='cb_re')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(button_yes, button_no, button_re)
    
    return keyboard
    
def get_keyboard_no_marks():
    button_fv = types.InlineKeyboardButton('⭐', callback_data='cb_fv')
    button_re = types.InlineKeyboardButton('🔄', callback_data='cb_re')

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(button_fv, button_re)
    
    return keyboard
    
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    
    db.add_message_to_database(message=message)
    
    if not BotConfig.TEST_MODE or message.from_user.id == BotConfig.CREATOR_ID:
        # response, responce_type = None, 'message'
        # try:
        response, responce_type, file_name = bot_state.process(message)
        # except Exception as e:
        #     response = f'Возникла ошибка: {e}'

        keyboard = get_keyboard()
        
        if response is not None:
            if responce_type == 'message':
                bot_message = bot.reply_to(message, response, reply_markup=keyboard)
            elif responce_type == 'photo':
                bot_message = bot.send_photo(message.chat.id, response, \
                                             reply_markup=keyboard, reply_to_message_id=message.message_id)
                
            db.add_message_to_database(bot_message, file_name=file_name)                
    else:
        pass
        # bot.reply_to(message, 'Я занят, напишите позднее!')
            
            
@bot.callback_query_handler(lambda q: q.data == 'cb_yes')
def cb_yes(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    db.add_reaction_to_database(call.message, call.from_user.id, likes=True)
    
    # bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_keyboard_no_marks())
    
    
@bot.callback_query_handler(lambda q: q.data == 'cb_no')
def cb_no(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    db.add_reaction_to_database(call.message, call.from_user.id, likes=False)
    
    # bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_keyboard_no_marks())
        
    
@bot.callback_query_handler(lambda q: q.data == 'cb_re')
def cb_re(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    message_id = call.message.message_id
    # bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    get_text_messages(call.message.reply_to_message)
    
    
@bot.callback_query_handler(lambda q: q.data == 'cb_fv')
def cb_fv(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    message_id = call.message.message_id
    
    db.add_message_to_favorite(call.message, call.from_user.id)
    
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, \
                                  message_id=call.message.message_id, reply_markup=get_keyboard_no_fav())
    
    
    
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
