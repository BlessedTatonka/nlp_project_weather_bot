import os
from src.text_processor import process
import requests
import json
import datetime
from deep_translator import GoogleTranslator


class WeatherConfig:
    API_KEY = os.getenv('WEATHER_API_TOKEN')
    BASE_URL = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline'


def get_weather_response(text, weather_request):
    location = weather_request['location']
    dates = weather_request['dates']

    if location == '':
        location = get_location(text)
        print(location)

    if len(dates) == 0:
        dates = get_dates(text)

    if location == '':
        response = 'Пожалуйста, укажите город'
    else:
        try:
            response = get_weather(location, dates)
        except Exception as e:
            print(e)
            response = 'API не смог найти такой город, видимо он очень маленький'
            location = 'None'

    weather_request['location'] = location
    weather_request['dates'] = dates
    return response


def get_location(text):
    location = ''

    with open('data/cities.json', 'r') as f:
        cities = json.load(f)

    for token in text.split(' '):
        prep_token = process(token)[0]
        if prep_token in cities.keys():
            location = cities[prep_token]    

    return location


## TODO REMOVE THIS WITH SOME LIBRARY LIKE NATASHA
accordance = {
    'сегодня': 0,
    'завтра': 1,
    'послезавтра': 2,
    'неделя': 6,
    'один': 0,
    'два': 1,
    'три': 2,
    'четыре': 3,
    'пять': 4,
    'шесть': 5,
    'семь': 6,
    'понедельник': (0 - datetime.datetime.today().weekday()) % 7,
    'вторник': (1 - datetime.datetime.today().weekday()) % 7,
    'среда': (2 - datetime.datetime.today().weekday()) % 7,
    'четверг': (3 - datetime.datetime.today().weekday()) % 7,
    'пятница': (4 - datetime.datetime.today().weekday()) % 7,
    'суббота': (5 - datetime.datetime.today().weekday()) % 7,
    'воскресенье': (6 - datetime.datetime.today().weekday()) % 7,
    'пн': (0 - datetime.datetime.today().weekday()) % 7,
    'вт': (1 - datetime.datetime.today().weekday()) % 7,
    'ср': (2 - datetime.datetime.today().weekday()) % 7,
    'чт': (3 - datetime.datetime.today().weekday()) % 7,
    'пт': (4 - datetime.datetime.today().weekday()) % 7,
    'сб': (5 - datetime.datetime.today().weekday()) % 7,
    'вс': (6 - datetime.datetime.today().weekday()) % 7,
    '1': 0,
    '2': 1,
    '3': 2,
    '4': 3,
    '5': 4,
    '6': 5,
    '7': 6,
}

def get_dates(text):
    from_date = datetime.date.today()
    to_date = datetime.date.today() + datetime.timedelta(days=6)

    for token in text.split(' '):
        prep_token = process(token)[0]
        for key in accordance.keys():
            if prep_token == process(key)[0]:
                to_date = datetime.date.today() + datetime.timedelta(days=accordance[key])

    return from_date, to_date


def get_weather(location, dates):
    from_date, to_date = dates

    query = f'{WeatherConfig.BASE_URL}/{location}/{from_date}/{to_date}?unitGroup=metric&include=days&&key={WeatherConfig.API_KEY}&contentType=json'
    request = requests.get(query)

    forecast = request.json()

    res = f'Погода {location}\n'
    delimeter = '-----------------------------\n'
    res += delimeter

    for day in forecast['days']:
        tempavg = day['temp']
        description = day['description']
        translated_description = GoogleTranslator(source='en', target='ru').translate(text=description)
        feelslike = day['feelslike']
        windspeed = day['windspeed']

        res += f'{day["datetime"]}\n'
        res += f'Средняя температура будет {tempavg}\n'
        res += f'{translated_description}\n'

        res += '' + delimeter

    return res

    