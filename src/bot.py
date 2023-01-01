from model.inference import predict_message_type, load_model

from modules.dialog_module import generate_conversation_response
from modules.weather_module import get_weather_response
from modules.ydisk_photo_module import get_photo_response

class UserState:
    def __init__(self, user_id, text):
        self.user_id = user_id
        self.text = text
        self.intent = None
        self.reset_weather_request()
        self.is_alive = False
        self.is_waiting = False
        self.conversation = []

    def reset_weather_request(self):
        self.weather_request = {
            'location': '',
            'dates': [],
        }

    def reset_user(self):
        self.text = None
        self.intent = None
        self.reset_weather_request()
        self.is_waiting = False
        self.conversation = []
        # self.is_alive = True

    def update(self, text, intent):
        self.text = text
        self.intent = intent


class BotState:
    def __init__(self):
        self.model = load_model('model/intents_classifier')
        self.user_states = {}


    def process(self, user_id, text):
        if user_id not in self.user_states.keys():
            self.user_states[user_id] = UserState(user_id, text)

        user = self.user_states[user_id]
        response, response_type = None, 'message'
        user.text = text

        if user.is_waiting:
            if user.intent == 'get_photo':
                response, response_type = self.process_get_photo(user)
            elif user.intent == 'get_weather':
                response = self.process_get_weather(user)
            else:
                # Unreachable situation
                user.reset_user()
        else:
            intent = self.get_intent(text)

            # if not user.is_alive and intent == 'greeting':
            #     response = self.process_greeting(user)
            # elif user.is_alive:
            if intent == 'get_photo':
                response, response_type = self.process_get_photo(user)
            # elif intent == 'goodbye':
            #     response = self.process_goodbye(user)
            # elif intent == 'get_weather':
            #     response = self.process_get_weather(user)
            else:
                response = self.process_no_category(user)

        return response, response_type


    def process_greeting(self, user):
        user.reset_user()
        user.is_alive = True
        response = 'Привет'
        return response


    def process_goodbye(self, user):
        user.reset_user()
        user.is_alive = False
        response = 'Пока'
        return response


    def process_get_photo(self, user):
        response = get_photo_response(user.text)
        # user.reset_user()   
        if response is not None:
            user.reset_user()
            return response, 'photo'
        else:
            if user.is_waiting:
                response = 'Прости, но таких фоток у меня нет'
                user.reset_user()
            else:
                response = 'Чьё фото прислать?'
                user.intent = 'get_photo'
                user.is_waiting = True

            return response, 'message'
        

    def process_get_weather(self, user):
        response = get_weather_response(user.text, user.weather_request)

        if user.weather_request['location'] != '':
            user.reset_user()
            return response
        else:
            if user.is_waiting:
                response = 'Я не знаю такого города'
                user.reset_user()
            else:
                response = 'Пожалуйста, укажите город'
                user.intent = 'get_weather'
                user.is_waiting = True

            return response, 'message'

        if user.weather_request['location'] == '':
            response = 'Пожалуйста, укажите город'
            user.intent = 'get_weather'
            user.is_waiting = True

        return response


    def process_no_category(self, user):
        # user.conversation = user.conversation[-3:]
        user.conversation = []
        user.conversation.append('@@ПЕРВЫЙ@@' + user.text)
        conversation = generate_conversation_response(user.conversation)
        response = conversation.split('@@ВТОРОЙ@@')[-1].split('@')[0]
        # user.conversation.append('@@ВТОРОЙ@@' + response)
        return response
        

    def get_intent(self, text):
        intent = predict_message_type(model=self.model, text=text)
        return intent
    