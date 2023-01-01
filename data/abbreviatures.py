import requests
import pandas as pd

url = 'https://base.garant.ru/12172539/1200328e1f3820fe59bbcbcc1d4380e3/#friends'
html = requests.get(url).content
df_list = pd.read_html(html, index_col=0)
df = df_list[0][3:].reset_index(drop=True)
df = df.rename(columns={1: 'республика', 2: 'город', 3: 'аббревиатура'})
df.to_csv('abbreviatures.csv')