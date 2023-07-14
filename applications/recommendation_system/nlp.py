
import numpy as np
import pandas as pd
import re
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer

class NaturalLanguageProcessor():
    def nlp(self,keywords):
        corpus = []
        cv = CountVectorizer()
        ps = PorterStemmer()
        for i in range(len(keywords)):
            data_word = re.sub('[^a-zA-ZÀ-ÿ]',' ',keywords[i])
            data_word = data_word.lower()
            data_word = data_word.split()
            data_word = [ps.stem(word) for word in data_word if not word in set(stopwords.words('spanish'))]
            data_word = ' '.join(data_word)
            corpus.append(data_word)
        X = cv.fit_transform(corpus).toarray()
        return X