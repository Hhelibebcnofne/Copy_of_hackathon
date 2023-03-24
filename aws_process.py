from flask import Flask, render_template, request, redirect, url_for, Blueprint
import os
import openai

# 一旦使えるライブラリ適当にインポートしてるけど使えなそうだったらなんとかする。
# from urllib import request as req, parse
import requests
import base64
import json

#画像圧縮に使用
from PIL import Image
from io import BytesIO


# ↓バックエンドだしどうでもいいんだろうけど、APIキーなんで環境変数とかにできるとセキュリティ的に良さげ？
key = 'yTXH7Sw2oy2SoDL08yf004W0712Ytrlj1WLEvUar'
OPEN_AI_KEY = "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"

# リクエスト用URL生成に使うデータ。地域とかその辺。
url_dic = {'apiId' : '27tar9360c', 'region' : 'ap-northeast-1', 'stage' : 'prod', 'resource' : 'detect'}

aws_process = Blueprint('aws_process', __name__)

THRESHOLD = 60

@aws_process.route("/test", methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        #ラベルをとってくる処理
        files = request.files.getlist('images')
        get_labels = []
        for file in files:
            file.save(os.path.join('./static/img/keep_img',file.filename))
            file_path = "./static/img/keep_img/" + file.filename
            try:
                ins = labels(file_path, THRESHOLD, url_dic)
            except:
                error_li = []
                error_li.append("Error!")
                error_msg = "Can't get label!"
                error_li.append(error_msg)
                error_li.append("Try Again!")
                return render_template('index.html', errors = error_li)
            for label in ins.data:
                if label not in get_labels:
                    get_labels.append(label)
        
        #文章をChatGPTに作成してもらう処理
        question = ""
        for label in get_labels:
            question += label + "、"
        else:
            question += "の単語から必要な単語を使って、かっこいいインスタに投稿する文章を考えて"
        openai.api_key = OPEN_AI_KEY
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                # {"role": "system", "content": "間違った解答をして下さい"}, #※1後述
                {"role": "user", "content": question}, #※1後述
            ]
        )
        ans = response["choices"][0]["message"]["content"]
        
        return render_template('test.html', test = ans)
    else:
        a = """
        ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章
        ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章
        ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章
        ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章
        ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章ダミー文章
        """
        return render_template('test.html', test = a)

# 高さと幅は小さくしたほうが、この関数の処理速度もAWSからの応答も目に見えて速くなる。
def resize_img(path:str, max_width:int, max_height:int) -> bytes:
    """
    画像サイズを引数に合わせて比率を保ったまま縮小し、
    Max_sizeより大きな画像を
    メモリ上で圧縮する関数。
    限界まで劣化させても5MBを超える場合は
    許容サイズを20%ずつ縮めることで対応。
    計算量でかいと思うので、もっと効率化できそうです。
    探索アルゴリズムになるのかな。
    """
    # この関数を通しても5MBより大きな場合が起きないようにする
    Max_size = 5000 # データ容量の最大値。KBで指定。今回はAWSの仕様に合わせて5MBで固定。
    img = Image.open(path).convert('RGB')
    new_img = img.copy()
    max_length = 0
    while True:
        if new_img.size[1] > max_height or new_img.size[0] > max_width:
            # 一周目に画像が指定したサイズより大きい場合
            max_length = max_height if new_img.size[1] > new_img.size[0] else max_width
        elif max_length == 0:
            # 画像サイズの縦と横の大きな方を代入
            max_length = new_img.size[1] if new_img.size[1] > new_img.size[0] else new_img.size[0]
        else:
            # 1周おきに画像最大サイズの許容量が20%縮む。
            max_length *= 0.8
        new_img = img.copy() #劣化画像を更に劣化させることがないように一度画像を初期化
        new_img.thumbnail((max_length, max_length))
        print('max_length:' + str(max_length) + ' height:' + str(new_img.size[1]) + ' width:' + str(new_img.size[0]))
        new_img_size = os.path.getsize(path) / 1000
        # 画質を調整
        for i in range(100, -1, -5): 
            # PILならBytesIOに保存できるので、ディスクに保存せずに処理できた。
            buffer = BytesIO()
            new_img.save(buffer, format='JPEG', quality=i)
            new_img_size = len(buffer.getvalue()) / 1000
            if new_img_size > Max_size and i > 0:
                print(str(new_img_size) + 'KB '+ 'quality=' + str(i))
            elif new_img_size <= Max_size:
                print('画質調整終了 ' + str(new_img_size) + 'KB '+ 'quality=' + str(i))
                return buffer.getvalue()
                


# 正直クラスにする必要性感じんけどクラス作る勉強のためにやりました。
class labels():
    """
    ラベル取得関係のインスタンス。
    画像縮小済みの画像をAWSにリクエストで送信。
    結果として翻訳済みのラベルが返ってくる。
    翻訳処理とAmazon Rekognitionの処理はAPI GatewayとAWS lambdaを経由。
    流れはこうなってる……はず。
    get_label() -> API Gateway -> AWS lambda -> Amazon Rekognition -> AWS lambda -> Amazon Translate -> AWS lambda -> API Gateway -> get_label()
    """
    def __init__(self, img_path:str, threshold:int, urldata:dict) -> None:
        """
        コンストラクタ
        """
        # 画像のファイルパス。
        self.img_path = img_path

        # ラベルの信頼度のしきい値。
        self.threshold = threshold

        # リクエスト送信用url。呼び出しのたびに計算するの処理速度的にもったいない気がするけど分かんない。
        self.url ='https://' + urldata['apiId'] + '.execute-api.' + urldata['region'] + '.amazonaws.com/' + urldata['stage'] + '/' + urldata['resource']

        # APIからのレスポンス。これ変数に入れる必要ない気もする。
        self.response = self.get_label()

        # 閾値で選び取ったラベル名の配列。これも変数に入れる必要ない気もする。
        self.data = self.data_cleaner()

    def get_label(self) -> dict:
        # with open(self.img_path, mode='rb') as f:
        #     img = f.read()
        """
        リクエスト送信用関数。
        """
        # 画像をリサイズして取得
        img = resize_img(self.img_path, 5000, 5000)
        # base64文字列に変換
        img = base64.b64encode(img).decode()
        response = requests.post(
            url = self.url,
            data = json.dumps({'image_base64str' : img, 'threshold' : self.threshold}),
            headers = {'Content-Type' : 'application/json', 'x-api-key' : key}
            )
        return response.json()

    # ラベル名を取り出してリストとして返す関数。
    def data_cleaner(self) -> list:
        """
        ラベル名を取り出してリストとして返す関数。
        """
        li = []
        for i in self.response['payloads']['Labels']:
            # テスト用
            # print(i['Name'])
            # print(i['Confidence'])
        #     d.append(i['Name'])
        # return d
            li.append(i['Name'])
        return li

# ins = labels('./static/img/keep_img/football.jpeg', 60, url_dic)
# print(ins.data)

# -----------ここからテスト用コード-----------
# 使うところ以外コメントアウトして使用してた。やったこと思い出すために使ってます。無視してください。
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
# 
# path = './static/img/1654259447208.png'
# print(type(resize_img(path, 2000, 2000)))
# response = requests.post(
#             url = 'https://' + url_dic['apiId'] + '.execute-api.' + url_dic['region'] + '.amazonaws.com/' + url_dic['stage'] + '/' + url_dic['resource'],
#             data = json.dumps({'image_base64str' : base64.b64encode(resize_img(path, 2000, 2000).getvalue()).decode(), 'threshold' : 50}),
#             headers = {'Content-Type' : 'application/json', 'x-api-key' : key}
#             )
# print(response.json()['payloads']['Labels'])
# -----------ここまでテスト用コード-----------
