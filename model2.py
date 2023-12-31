# -*- coding: utf-8 -*-
"""ModelTraining.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1HUYDfaY_YIVBqbqwmMhgug5pk2SPwBtM
"""

import pandas as pd
import nltk
import pickle
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv("Data/spotify_millsongdata.csv")
df = df.drop('link',axis=1).reset_index(drop = True)
df = df.sample(5000).reset_index(drop=True)

df['text'] = df['text'].str.lower().replace(r'^\w\s', ' ').replace(r'\n', ' ', regex = True)

stemmer = PorterStemmer()

def tokenization(txt):
    tokens = nltk.word_tokenize(txt)
    stemming = [stemmer.stem(w) for w in tokens]
    return " ".join(stemming)

df['text'] = df['text'].apply(lambda x: tokenization(x))

tfid = TfidfVectorizer(analyzer='word', stop_words='english')

matrix = tfid.fit_transform(df['text'])

similarity = cosine_similarity(matrix)

def recommender(song_name):
  idx = df[df['song']==song_name].index[0]
  distance = sorted(list(enumerate(similarity[idx])), reverse=True, key = lambda x : x[1])
  songs = []
  for s_id in distance[1:6]:
    songs.append(df.iloc[s_id[0]].song)
  return songs

# import pickle

pickle.dump(similarity, open("similariry.pkl", "wb"))

pickle.dump(df, open("df.pkl", "wb"))

