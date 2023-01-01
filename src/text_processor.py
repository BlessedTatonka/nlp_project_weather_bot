import spacy
import nltk
from nltk.tokenize import word_tokenize
from autocorrect import Speller
from nltk.stem.snowball import SnowballStemmer

class _Preload():
    def __init__(self):
        nltk.download('punkt')
        # nltk.download('stopwords')
        self.spell = Speller(lang='ru')
        self.stemmer = SnowballStemmer("russian")

p = _Preload()

def process(text, correct=True):
    text = text.lower()
    word_tokens = word_tokenize(text)
    for i in range(len(word_tokens)):
        if word_tokens[i][0].isalpha():
            word_tokens[i] = word_tokens[i][0].upper() + word_tokens[i][1:]

    output = [w for w in word_tokens]
    if correct:
        output = list(map(p.spell, output))
    # output = [morph.parse(w)[0].normal_form for w in output]
    output = [p.stemmer.stem(word) for word in output]

    return output