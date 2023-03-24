from flask import Flask, render_template, request, redirect, url_for, Blueprint
import os

# 一旦使えるライブラリ適当にインポートしてるけど使えなそうだったらなんとかする。
# from urllib import request as req, parse
import requests
import base64
import json

#画像圧縮に使用
from PIL import Image
import cv2
import numpy as np

from io import BytesIO
import matplotlib.pyplot as plt


# ↓バックエンドだしどうでもいいんだろうけど、APIキーなんで環境変数とかにできるとセキュリティ的に良さげ？
key = 'yTXH7Sw2oy2SoDL08yf004W0712Ytrlj1WLEvUar'

# リクエスト用URL生成に使うデータ。地域とかその辺。
url_dic = {'apiId' : '27tar9360c', 'region' : 'ap-northeast-1', 'stage' : 'prod', 'resource' : 'detect'}

aws_process = Blueprint('aws_process', __name__)

@aws_process.route("/test", methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        test = request.form.get('test')
        file = request.files['img']
        file.save(os.path.join('./static/img',file.filename))
        return render_template('test.html', test = file.filename)
    else:
        return render_template('index.html')

# 正直クラスにする必要性感じんけどクラス作る勉強のためにやりました。
class labels():
    def __init__(self, img_path:str, threshold:int, urldata:dict) -> None:
        # 画像のファイルパス。
        self.img_path = img_path
        
        # ラベルの信頼度のしきい値。
        self.threshold = threshold

        # リクエスト送信用url。呼び出しのたびに計算するの処理速度的にもったいない気がするけど分かんない。
        self.url ='https://' + urldata['apiId'] + '.execute-api.' + urldata['region'] + '.amazonaws.com/' + urldata['stage'] + '/' + urldata['resource']

        # APIからのレスポンス。
        self.response = self.get_label()

        # 閾値で選び取ったラベル名の配列。
        self.data = self.data_cleaner()

    # リクエスト送信用関数。
    def get_label(self) -> dict:
        with open(self.img_path, mode='rb') as f:
            img = f.read()
        img = base64.b64encode(img).decode()
        # print(img)
        response = requests.post(
            url = self.url,
            data = json.dumps({'image_base64str' : img, 'threshold' : self.threshold}),
            headers = {'Content-Type' : 'application/json', 'x-api-key' : key}
            )
        return response.json()

    # ラベル名を取り出してリストとして返す関数。
    def data_cleaner(self) -> list:
        li = []
        for i in self.response['payloads']['Labels']:
            # テスト用
            # print(i['Name'])
            # print(i['Confidence'])
            li.append(i['Name'])
        return li
    
# -----------ここからテスト用コード-----------
# 使うところ以外コメントアウトして使用してた。無視してください。
# ins = labels('./static/img/1654259447208.png', 60, url_dic)
# print(ins.data)

# im = Image.open('./static/img/flask.png').convert('RGB')
# # # img_array = np.array(im)
# buffer = BytesIO()
# im.save(
#     buffer,
#     format='JPEG',
#     quality=100)

# im.save(
#     './static/img/adada.jpg',
#     format='JPEG',
#     quality=100)
# print(os.path.getsize('./static/img/adada.jpg'))
# print(len(buffer.getvalue()))
# Image.fromarray(img_array).save(
#     buffer,
#     format='JPEG',
#     quality=10)
# ここが
# img2 = Image.open(buffer)
# img_array2 = np.array(img2)
# print(len(base64.b64encode(buffer.getvalue()).decode()))
# print(buffer.getvalue())
# print(len(base64.b64encode(img2).decode()))


# ins = labels('./static/img/flask.png', 60, url_dic)
# print(ins.data)
# img = cv2.imread('./static/img/flask.png')
# print(img)
# ret, encoded = cv2.imencode(".png", img,  [int(cv2.IMWRITE_PNG_COMPRESSION ), 10])
# print(ret)
# print(encoded)
# print(base64.b64encode(encoded).decode())
# aa = cv2.imdecode(encoded, flags=cv2.IMREAD_COLOR)
# print(base64.b64encode(encoded).decode())
# print(len(base64.b64encode(encoded).decode()))

# response = requests.post(
#             url = 'https://' + url_dic['apiId'] + '.execute-api.' + url_dic['region'] + '.amazonaws.com/' + url_dic['stage'] + '/' + url_dic['resource'],
#             data = json.dumps({'image_base64str' : base64.b64encode(buffer.getvalue()).decode(), 'threshold' : 60}),
#             headers = {'Content-Type' : 'application/json', 'x-api-key' : key}
#             )
# print(response.json()['payloads']['Labels'])
# print(aa)
# with open('./static/img/flask.png', mode='rb') as f:
#     img = f.read()
# print(img)
# img = base64.b64encode(img).decode()
# print(len(img))
# print(img)
# -----------ここまでテスト用コード-----------

# リサイズしたい画像のパス
path = './static/img/1654259447208.png'
def resize_img(path:str, max_height:int, max_width:int) -> object:
    Max_size = 5000 # データ容量の最大値。KBで指定。今回は5MBで固定。
    img = Image.open(path).convert('RGB')
    new_img = img.copy()
    new_img.thumbnail((max_height, max_width))
    new_img_size = os.path.getsize(path) / 1000
    # 画質を調整
    for i in range(100, -1, -5): 
        # PILならBytesIOに保存できるので、ディスクに保存せずに処理できた。
        buffer = BytesIO()
        new_img.save(buffer, format='JPEG', quality=i)
        new_img_size = len(buffer.getvalue()) / 1000
        if new_img_size > Max_size and i > 0:
            print(str(new_img_size) + 'KB '+ 'quality=' + str(i))
        else:
            print('画質調整終了 ' + str(new_img_size) + 'KB '+ 'quality=' + str(i))
            break
    # if img
    return buffer
    # PNGをJPEGに変換したくない場合、以下のコードを使う。PNGとJPEG以外非対応。
    # RGBAに対応出来るようになるものの、データ量が大きくなりやすいので、使用は非推奨。
    # print(img.format)
    # if img.format == 'JPEG':
    #     for i in range(100, -1, -5): 
    #         buffer = BytesIO()
    #         new_img.save(buffer, format='JPEG', quality=i)
    #         new_img_size = len(buffer.getvalue()) / 1000
    #         if new_img_size > Max_size and i > 0:
    #             print(str(new_img_size) + 'KB '+ 'quality=' + str(i))
    #         else:
    #             print('画質調整終了 ' + str(new_img_size) + 'KB '+ 'quality=' + str(i))
    #             break
    # elif img.format == 'PNG':
    #     for i in range(10): 
    #         buffer = BytesIO()
    #         new_img.save(buffer, format='PNG', compress_level=i)
    #         new_img_size = len(buffer.getvalue()) / 1000
    #         if new_img_size > Max_size and i < 10:
    #             print(str(new_img_size) + 'KB '+ 'compress_level=' + str(i))
    #         else:
    #             print('画質調整終了 ' + str(new_img_size) + 'KB '+ 'compress_level=' + str(i))
    #             break

print(type(resize_img(path, 2000, 2000)))
# 以下テスト用
# response = requests.post(
#             url = 'https://' + url_dic['apiId'] + '.execute-api.' + url_dic['region'] + '.amazonaws.com/' + url_dic['stage'] + '/' + url_dic['resource'],
#             data = json.dumps({'image_base64str' : base64.b64encode(resize_img(path, 2000, 2000).getvalue()).decode(), 'threshold' : 50}),
#             headers = {'Content-Type' : 'application/json', 'x-api-key' : key}
#             )
# print(response.json()['payloads']['Labels'])