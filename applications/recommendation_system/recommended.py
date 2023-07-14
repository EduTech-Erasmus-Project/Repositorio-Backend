from applications.recommendation_system.dataset_generator import DataSetGenerator
from nltk.util import pr
import numpy as np
import pandas as pd
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer
tfidf = TfidfVectorizer(stop_words=stopwords.words('spanish'))
# from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import string
dataset_generator = DataSetGenerator()
class ItemsRecomended():
  def user_learning_object_recomended_liked(self,user):
    try:
      df_user_oa_liked = dataset_generator.user_learning_object_liked(user)
      results = learning_object_recomended(int(df_user_oa_liked['learning_object']))
      return results
    except:
      return []

def learning_object_recomended(loId):
  df = dataset_generator.learning_object_metadata().rename({'id':'loId','general_keyword':'keywords','general_title':'title'}, axis=1)
  title = str(df.iloc[loId]['title'])
  df['keywords']= df.keywords.str.replace('[{}]'.format(string.punctuation),' ')
  df['keywords']= df['keywords'].fillna('')
  tfidf_matrix = tfidf.fit_transform(df['keywords'])
  cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
  index =  pd.Series(df.index, index=df['title']).drop_duplicates()
  def get_recommendations(title=title, cosine_sim=cosine_sim):
    idx = index[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6]
    oa_index = [i[0] for i in sim_scores]
    return df['loId'].iloc[oa_index].tolist()
  return get_recommendations()
        
# def get_mse(preds,actuals):
#     return mean_squared_error(preds, actuals,squared=False)