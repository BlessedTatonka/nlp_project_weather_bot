import pandas as pd
import numpy as np
import glob
import os


def get_data():
    data = pd.DataFrame(columns={0, 'category'})

    for cat in glob.glob("data/intents/*.txt"):
        cat_name = os.path.basename(cat).split('.')[0]
        tmp_data = pd.read_csv(cat, header=None)
        tmp_data['category'] = cat_name
        data = data.append(tmp_data)

    data = data.rename(columns={0: 'message'})

    print(data)
    labels_ord = np.array(['get_photo', 'get_weather', 'goodbye', 'greeting', 'no_category'])

    number_of_categories = len(labels_ord)
    data['label'] = data['category'].apply(lambda x: np.where(labels_ord == x)[0][0])

    return number_of_categories, data