import csv

import numpy as np
import pandas as pd
from scipy import sparse
from tqdm import tqdm
from sklearn.metrics.pairwise import pairwise_distances

u_data_org = pd.read_csv('./u.data', sep='\t', names=['user_id','item_id', 'rating', 'timestamp'])

# ユーザ数✖️アイテム数の配列を作成する(R)
# shape = (u_data_org.max().loc['user_id'], u_data_org.max().loc['item_id'])
# R = np.zeros(shape)
# for i in u_data_org.index:
#     row = u_data_org.loc[i]
#     R[row['user_id'] -1 , row['item_id'] - 1] = row['rating']
# print(R)

# ユーザ数×評価値のデータ
u_data_train = pd.read_csv('./ua.base', names=['user_id', 'item_id', 'rating', 'timestamp'], sep='\t')
u_data_test = pd.read_csv('./ua.test', names=['user_id', 'item_id', 'rating', 'timestamp'], sep='\t')

# アイテム同士の類似度を計算するために学習データをitem_id✖️user_idの行列に変換する
items = u_data_org.sort_values('item_id').item_id.unique()
users = u_data_org.user_id.unique()
rating_matrix_item = np.zeros([len(items), len(users)])

for item_id in tqdm(range(1, len(items))):
    users_item = u_data_train[u_data_train['item_id'] == item_id].sort_values('user_id').user_id.unique()
    for user_id in users_item:
        try:
            user_rate = u_data_train[(u_data_train['item_id'] == item_id) & (u_data_train['user_id'] == user_id)].loc[:, 'rating']
        except:
            user_rate = 0
        rating_matrix_item[item_id-1, user_id-1] = user_rate


# item x userの評価したかどうか{0, 1}がわかる行列作成
rating_matrix_calc = rating_matrix_item.copy()
rating_matrix_calc[rating_matrix_calc != 0] = 1

# 評価していないアイテムに1が立つ行列を作成。後で使う
rating_matrix_train = np.abs(rating_matrix_calc - 1)

similarity_matrix = 1 - pairwise_distances(rating_matrix_item, metric='cosine')
np.fill_diagonal(similarity_matrix, 0)

# print(similarity_matrix)

user_id = 100
hits = 0

# 各ユーザの評価値を抜き出し「類似度×評価点」を算出
rating_matrix_user = rating_matrix_item[:, user_id - 1]
pred_rating_user = similarity_matrix * rating_matrix_user
# アイテム（行）ごとに「類似度×評価点」を合計
pred_rating_user = pred_rating_user.sum(axis=1)

# ユーザが既に評価したアイテムのスコアはゼロに直す
pred_rating_user_item = pred_rating_user * rating_matrix_train[:,user_id - 1]

#ここからレコメンドされたアイテムがどれだけあっていたかを評価していく
recommend_list = np.argsort(pred_rating_user_item)[::-1][:10] + 1
purchase_list_user = u_data_test[u_data_test.user_id == user_id].loc[:, 'item_id'].unique()
for item_id in recommend_list:
    if item_id in purchase_list_user:
        hits += 1
pre = hits / 10.0

# print('Recommend list:', recommend_list)
# print('Test Rated list:', purchase_list_user)
# print('Precision:', str(pre))

precision_list = []
recall_list = []
user_list_test = u_data_test.sort_values('user_id').user_id.unique()

for user_id in tqdm(user_list_test):
    hits = 0
    # 各ユーザの評価値を抜き出し「類似度×評価点」を算出
    rating_matrix_user = rating_matrix_item[:, user_id - 1]
    pred_rating_user = similarity_matrix * rating_matrix_user

    # アイテム（行）ごとに「類似度×評価点」を合計
    pred_rating_user_item = pred_rating_user * rating_matrix_train[:,user_id - 1]

    # ユーザが既に評価したアイテムのスコアはゼロに直す
    pred_rating_user_item[np.isnan(pred_rating_user_item)] = 0

    #ここからレコメンドされたアイテムがどれだけあっていたかを評価していく
    recommend_list = np.argsort(pred_rating_user_item)[::-1][:10] + 1
    purchase_list_user = u_data_test[u_data_test.user_id == user_id].loc[:, 'item_id'].unique()
    if len(purchase_list_user) == 0:
        continue
    for item_id in recommend_list:
        if item_id in purchase_list_user:
            hits += 1
    pre = hits / 10.0
    precision_list.append(pre)

# 全体の精度検証
precision = sum(precision_list) / len(precision_list)
print('Precision:', precision)