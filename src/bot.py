from model.inference import predict_message_type, load_model

from modules.dialog_module import generate_conversation_response
from modules.weather_module import get_weather_response
from modules.ydisk_photo_module import get_photo_response
from modules.diffuser_module import generate_image_response 

from datetime import datetime
import random


class UserState:
    def __init__(self, user_id, text):
        self.user_id = user_id
        self.text = [text]
        self.intent = None
        self.is_waiting = False
        self.result = None

    def reset_user(self):
        self.text = []
        self.intent = None
        self.is_waiting = False

        
class BotState:
    def __init__(self):
        self.model = load_model('model/get_photo+generate_photo+no_category')
        self.user_states = {}


    def process(self, message):
        user_id, text = message.from_user.id, message.text
        if user_id not in self.user_states.keys():
            self.user_states[user_id] = UserState(user_id, text)

        user = self.user_states[user_id]
        intent = self.get_intent(text)
        
        
        if text.lower() in ['нет', 'еще', 'другую', 'дальше', 'ещё']:
            user.text.append(text)
            if user.intent == 'get_photo':
                response, response_type, file_name = self.process_get_photo(user)
            elif user.intent == 'generate_photo':
                response, response_type, file_name = self.process_generate_image(user)
            # PROCESS THIS SITUATION
            # else
        else:
            user.reset_user()
            user.intent = intent
            user.text.append(text)
            
            if user.intent == 'get_photo':
                response, response_type, file_name = self.process_get_photo(user)
            elif user.intent == 'generate_photo':
                response, response_type, file_name = self.process_generate_image(user)
            else:
                response, response_type, file_name = self.process_no_category(user)
                
        return response, response_type, file_name

    
    def get_intent(self, text):
        intent = predict_message_type(model=self.model, text=text)
        return intent
    

    def process_get_photo(self, user):
        response, file_name = get_photo_response(user.text[0], k=random.randint(0, 6))
        
        return response, 'photo', file_name
        
    
    def process_generate_image(self, user):
        response, file_name = generate_image_response(user.text[0])
        
        return response, 'photo', file_name


    def process_no_category(self, user):
        user.conversation = []
        user.conversation.append('@@ПЕРВЫЙ@@' + user.text[-1])
        conversation = generate_conversation_response(user.conversation)
        response = conversation.split('@@ВТОРОЙ@@')[-1].split('@')[0]
        user.reset_user()
        return response, 'message', None
    