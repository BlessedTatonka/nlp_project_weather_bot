from src.text_processor import process
import requests
import random
import json
import datetime
from deep_translator import GoogleTranslator
import os
import pandas as pd
import sentence_transformers


class YDiskConfig:
    API_KEY = os.getenv('YDISK_API_TOKEN')
    BASE_REQUEST = 'https://cloud-api.yandex.net/v1/disk/resources'
    ROOT_DIR = 'photo/photos_hse_nlp'
    headers = {
        'Accept': 'application/json',
        'Authorization': f'{API_KEY}'
    }
    model = sentence_transformers.SentenceTransformer('inkoziev/sbert_pq')
    embeddings = None


def get_photo_response(text):
    text = ' '.join(process(text))

    if YDiskConfig.embeddings is None:
        tags = pd.read_excel(get_tags().json()['file'])
        descriptions = tags['description'].values
        embeddings = YDiskConfig.model.encode(descriptions)
        YDiskConfig.embeddings = embeddings
        YDiskConfig.tags = tags
 
    text = YDiskConfig.model.encode([text * 3])

    cos_sim = sentence_transformers.util.cos_sim(text, YDiskConfig.embeddings)[0]

    all_sentence_combinations = []
    for i in range(len(cos_sim)):
        all_sentence_combinations.append([cos_sim[i], i])

    all_sentence_combinations = sorted(all_sentence_combinations, key=lambda x: x[0], reverse=True)

    print(YDiskConfig.tags['filename'].iloc[all_sentence_combinations[0][1]])
    if all_sentence_combinations[0][0] >= 0.3:
        try:
            return get_photo_by_path(YDiskConfig.tags['filename'].iloc[all_sentence_combinations[0][1]])
        except:
            return None
    else:
        return None

# def get_photo_response(text):
#     categories = get_categories()

#     for token in text.split(' '):
#         prep_token = process(token, correct=False)[0]
#         print(f'prep_token for {text} is {prep_token}')
#         for key in categories.keys():
#             if (prep_token in key or key in prep_token) and len(prep_token) > 2:
#                 return get_photo(categories[key])

#     return None


def get_categories():
    response = requests.get(f'{YDiskConfig.BASE_REQUEST}?path={YDiskConfig.ROOT_DIR}&limit=1000',
                                headers=YDiskConfig.headers)
    values = []
    for item in response.json()['_embedded']['items']:
        values.append(item['name'])

    categories = {}
    for item in values:
        categories[process(item, correct=False)[0]] = item

    return categories


def get_photo_by_path(filepath):
    response = requests.get(f'{YDiskConfig.BASE_REQUEST}?path={YDiskConfig.ROOT_DIR}/{filepath}.jpeg',
                                headers=YDiskConfig.headers)

    return response.json()['file']


# def get_photo(category, k=None):
#     response = requests.get(f'{YDiskConfig.BASE_REQUEST}?path={YDiskConfig.ROOT_DIR}/{category}&limit=1000',
#                                 headers=YDiskConfig.headers)
#     elements = response.json()['_embedded']['items']

#     category_len = response.json()['_embedded']['total'] 

#     if k is None:
#         k = random.randint(0, category_len - 1)

#     return elements[k]['file']


def get_tags():
    response = requests.get(f'{YDiskConfig.BASE_REQUEST}?path={YDiskConfig.ROOT_DIR}/tags.xlsx',
                                headers=YDiskConfig.headers)
    # elements = response.json()['_embedded']['items']

    # category_len = response.json()['_embedded']['total'] 

    # if k is None:
    #     k = random.randint(0, category_len - 1)

    return response
