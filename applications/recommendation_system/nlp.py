"""Helpers NLP legacy para recommendation_system.

Este módulo implementa un preprocesamiento muy básico de keywords:
- limpieza por regex
- lowercasing
- eliminacion de stopwords en español
- stemming con `PorterStemmer`
- vectorizacion con `CountVectorizer`

Hoy no parece ser la pieza principal del endpoint de recomendaciones, que usa
TF-IDF en `recommended.py`, pero sigue documentado porque podría alimentar
flujos experimentales o legado dentro del módulo.
"""

import numpy as np
import pandas as pd
import re
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer


class NaturalLanguageProcessor():
    """Procesador simple de keywords para obtener una matriz bag-of-words.

    Riesgos y supuestos actuales:
    - ejecuta `nltk.download('stopwords')` al importar el modulo
    - usa `PorterStemmer`, que está más orientado a ingles que a español
    - asume que `keywords` es una secuencia indexable de strings
    """

    def nlp(self,keywords):
        """Normaliza keywords y devuelve una matriz numérica de frecuencias.

        El resultado es un `ndarray` generado por `CountVectorizer`, donde cada
        fila representa el texto procesado de un elemento de `keywords`.
        """

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