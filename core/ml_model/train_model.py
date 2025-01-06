import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
import joblib
import os
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# 現在のスクリプトのディレクトリを取得
current_dir = os.path.dirname(os.path.abspath(__file__))

# CSVファイルの読み込み
csv_path = os.path.join(current_dir, 'tasks.csv')
df = pd.read_csv(csv_path)

# テキストデータの前処理
def preprocess_text(text):
    text = text.lower()  # 小文字化
    text = re.sub(r'\d+', '', text)  # 数字の削除
    text = re.sub(r'[^\w\s]', '', text)  # 句読点の削除
    text = text.strip()  # 前後の空白を削除
    stop_words = set(stopwords.words('japanese'))
    lemmatizer = WordNetLemmatizer()
    text = ' '.join([lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words])
    return text

df['task_name'] = df['task_name'].apply(preprocess_text)

# ラベルを数値に変換するマッピング
grade_mapping = {'A': 1, 'B': 2, 'C': 3}
priority_mapping = {'A': 1, 'B': 2, 'C': 3}

# ラベルを数値に変換
df['grade'] = df['grade'].map(grade_mapping)
df['priority'] = df['priority'].map(priority_mapping)

# 特徴量とターゲットの分割
X = df['task_name']
y_tag = df['tag']
y_grade = df['grade']
y_priority = df['priority']

# パイプラインの作成とハイパーパラメータのチューニング
pipeline_tag = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', RandomForestClassifier())
])

param_grid = {
    'tfidf__max_df': [0.8, 0.9, 1.0],
    'tfidf__ngram_range': [(1, 1), (1, 2)],
    'clf__n_estimators': [100, 200],
    'clf__max_depth': [None, 10, 20]
}

grid_search_tag = GridSearchCV(pipeline_tag, param_grid, cv=5, n_jobs=-1, verbose=1)
grid_search_tag.fit(X, y_tag)

# 最適なモデルで再トレーニング
best_pipeline_tag = grid_search_tag.best_estimator_
best_pipeline_tag.fit(X, y_tag)

# モデルの保存
model_dir = os.path.join(current_dir, 'ml_model')
os.makedirs(model_dir, exist_ok=True)
joblib.dump(best_pipeline_tag, os.path.join(model_dir, 'tag_model.pkl'))