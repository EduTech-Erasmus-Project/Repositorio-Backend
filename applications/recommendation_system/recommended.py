"""Helpers de recomendación por similitud para recommendation_system.

Este módulo implementa la rama basada en contenido del recomendador: parte del
ultimo OA marcado como liked por el usuario y busca objetos similares usando
TF-IDF sobre `general_keyword`. La salida no construye el queryset final del
endpoint; solo devuelve ids candidatos que luego otras capas filtran.
"""

from applications.recommendation_system.dataset_generator import DataSetGenerator
from functools import lru_cache
import logging
from nltk.util import pr
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import string
dataset_generator = DataSetGenerator()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_spanish_stopwords():
  """Carga stopwords en español y las cachea para reutilizarlas.

  Si el recurso de NLTK no está instalado, el módulo sigue funcionando sin
  stopwords en lugar de fallar durante el cálculo de similitud.
  """

  try:
    return list(stopwords.words('spanish'))
  except LookupError:
    logger.warning("NLTK stopwords no esta disponible; se continua sin stopwords en recommendation_system")
    return None


def build_tfidf_vectorizer():
  """Construye el vectorizador TF-IDF con las stopwords disponibles."""

  return TfidfVectorizer(stop_words=get_spanish_stopwords())


class ItemsRecomended():
  """Agrupa helpers de recomendación derivados del comportamiento del usuario."""

  def user_learning_object_recomended_liked(self,user):
    """Recomienda OAs similares al último objeto liked por el usuario.

    La fuente real del OA semilla es `dataset_generator.user_learning_object_liked`.
    Si no hay interaccion liked o el dataset no tiene la forma esperada, el
    método responde `[]` y deja que la vista degrade silenciosamente.
    """

    try:
      df_user_oa_liked = dataset_generator.user_learning_object_liked(user)
      if not isinstance(df_user_oa_liked, pd.DataFrame) or df_user_oa_liked.empty:
        return []
      if 'learning_object' not in df_user_oa_liked.columns:
        return []
      results = learning_object_recomended(int(df_user_oa_liked['learning_object'].iloc[0]))
      return results
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
      logger.exception("Error calculando recomendaciones por likes para el usuario %s", getattr(user, 'id', None))
      return []


def learning_object_recomended(loId):
  """Calcula similitud entre OAs a partir de `general_keyword`.

  Flujo:
  - obtiene metadata base de OAs públicos
  - renombra columnas a un esquema interno (`loId`, `keywords`, `title`)
  - vectoriza `keywords` con TF-IDF
  - calcula similitud coseno mediante `linear_kernel`
  - devuelve hasta 5 ids de OAs más similares al OA semilla

  Supuestos y riesgos:
  - usa `title` como índice auxiliar; si hay títulos duplicados toma la primera
    coincidencia
  - depende de que `general_keyword` tenga contenido útil para comparar
  - ante metadata faltante o tipos inesperados devuelve `[]`
  """

  df = dataset_generator.learning_object_metadata()
  if not isinstance(df, pd.DataFrame) or df.empty:
    return []
  df = df.rename({'id':'loId','general_keyword':'keywords','general_title':'title'}, axis=1)
  required_columns = {'loId', 'keywords', 'title'}
  if not required_columns.issubset(df.columns):
    return []
  row = df.loc[df['loId'] == loId]
  if row.empty:
    return []
  try:
    title = str(row.iloc[0]['title'])
    df['keywords']= df['keywords'].fillna('').astype(str).str.replace('[{}]'.format(string.punctuation),' ', regex=True)
    tfidf = build_tfidf_vectorizer()
    tfidf_matrix = tfidf.fit_transform(df['keywords'])
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    index =  pd.Series(df.index, index=df['title']).drop_duplicates()

    def get_recommendations(title=title, cosine_sim=cosine_sim):
      """Extrae ids de los OAs más similares al título de referencia."""

      idx = index[title]
      if isinstance(idx, pd.Series):
        idx = idx.iloc[0]
      sim_scores = list(enumerate(cosine_sim[idx]))
      sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
      sim_scores = sim_scores[1:6]
      oa_index = [i[0] for i in sim_scores]
      return df['loId'].iloc[oa_index].tolist()
    return get_recommendations()
  except (AttributeError, KeyError, TypeError, ValueError, IndexError):
    logger.exception("Error calculando recomendaciones por similitud para el OA %s", loId)
    return []
        
# def get_mse(preds,actuals):
#     return mean_squared_error(preds, actuals,squared=False)
