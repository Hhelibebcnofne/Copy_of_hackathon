from flask import Flask, render_template, request, redirect, url_for, Blueprint
import os

# 一旦使えるライブラリ適当にインポートしてるけど使えなそうだったらなんとかする。
# from urllib import request as req, parse
import requests
import base64
import json
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
        file_path = "./static/img/" + file.filename
        ins = labels('./static/img/flask.png', 80, url_dic)
        return render_template('test.html', test = file.filename)
    else:
        return render_template('index.html')

# 正直クラスにする必要性感じんけどクラス作る勉強のためにやりました。ゲッターとかセッターとか面倒くさいし知らん。
class labels():
    def __init__(self, img_path, threshold, urldata):
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
    def get_label(self):
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

    # ラベル名を取り出して配列として返す関数。
    def data_cleaner(self):
        d = []
        for i in self.response['payloads']['Labels']:
            # テスト用
            # print(i['Name'])
            # print(i['Confidence'])
            d.append(i['Name'])
        return d

print(ins.data)
