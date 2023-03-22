from flask import Flask, render_template, request, redirect, url_for, Blueprint
import os

# 一旦使えるライブラリ適当にインポートしてるけど使えなそうだったらなんとかする。
# from urllib import request as req, parse
import requests
import base64
import json
#↓バックエンドだしどうでもいいんだろうけど、APIキーなんで環境変数とかにできるとセキュリティ的に良さげ？
key = 'yTXH7Sw2oy2SoDL08yf004W0712Ytrlj1WLEvUar'

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


def get_label(img_path):
    
    with open(img_path, mode='rb') as f:
        img = f.read()
    img = base64.b64encode(img).decode()
    # print(img)
    response = requests.post(
        url = 'https://27tar9360c.execute-api.ap-northeast-1.amazonaws.com/prod/detect',
        data = json.dumps({'image_base64str' : img, 'threshold' : 90}),
        headers = {'Content-Type' : 'application/json', 'x-api-key' : key}
        )
    return response.json()

img_path = './static/img/flask.png'
print(get_label(img_path))
print(type(get_label(img_path)))