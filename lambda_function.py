# -*- coding: utf-8 -*-
"""
Rekognitionでラベルを検出するための、Lambda上で実行するコード。
Method: POST
"""
import json
import boto3
from typing import Union, Tuple
from datetime import datetime
import botocore.exceptions
import base64
import re

REKOGNITION_CLIENT = boto3.client('rekognition')
TRANSLATE_CLIENT = boto3.client('translate')

# 翻訳元言語と翻訳後言語
SRC_LANG = 'en'
TRG_LANG = 'ja'

# リクエストボディに必須の値(name)とその型(type)の定義
REQUIRED_KEYS: list = [{'name': 'image_base64str', 'type': (str,)}]
OPTIONAL_KEYS: list = [{'name': 'threshold', 'type': (float, int)}]

class getLabels():
     def __init__(self):
          self.rekognition_client = REKOGNITION_CLIENT
          self.required_keys = REQUIRED_KEYS
          self.optional_keys = OPTIONAL_KEYS
          self.translate_client = TRANSLATE_CLIENT
          self.src_lang = SRC_LANG
          self.trg_lang = TRG_LANG
     def make_timestamp(self) -> str: 
          """
          タイムスタンプ作成
          """
          date_now = datetime.now()
          return str(date_now.strftime('%Y-%m-%d %H:%M:%S'))

     def create_response(self, data: dict) -> dict:
          """
          Rekognition結果を解析し、Response Bodyのデータを作成する
          """
          print('[DEBUG]create_response()')
          payloads: dict = {}
          payloads['timestamp'] = self.make_timestamp()
          payloads.update(data)
          return self.make_response(200, '[SUCCEEDED]Rekognition done', payloads)

     def decode_base64_to_binary(self, image_base64str: str) -> bytes:
          """
          base64のデータをバイナリデータに変換する
          """
          print('[DEBUG]decode_base64_to_binary()')
          # 画像データから不要な値を抜き出す(コンマがない場合は不要な値がないとし、全文字列を利用)
          image_base64str = image_base64str[image_base64str.find(',') + 1 :]
          return base64.b64decode(image_base64str)

     def detect_labels(self, image_binary: bytes, threshold: float = None) -> dict:
          """
          ラベルを取得する
          """
          print('[DEBUG]detect_labels()')
          try:
               detect_result = self.rekognition_client.detect_labels(
                    Image={
                         'Bytes': image_binary
                    },
                    MinConfidence=threshold
               )
               # return self.create_response(detect_result)
               return self.translate(detect_result)
          # エラー
          except Exception as error:
               print('[DEBUG]: {}'.format(error))
               error_code = error.response['Error']['Code']
               return self.make_response(500, '[FAILED]{}'.format(error))
               
     def translate(self,responses):
          """
          翻訳用関数
          """
          print('[DEBUG]translate()')
          text = ''
          # Text to translate
          for i in responses['Labels']:
               text += i['Name'] + ','
          print(text)
          # From Japanese to English
          # while len(text.encode('utf-8')) > 5000:
          #   text = text[:-1]

          # From English to Japanese
          # while len(text) > 5000:
          #      text = text[:-1]
          try:
               trans_response = self.translate_client.translate_text(
                    Text=text,
                    SourceLanguageCode=self.src_lang,
                    TargetLanguageCode=self.trg_lang
               )
               print(trans_response.get('TranslatedText'))
               aa = re.split('[ ,、　]+', trans_response.get('TranslatedText'))
               # minで数が小さい方を使うことで、区切り方などの問題で数字が合わなかったときの応急処置。
               for i in range(min(len(responses['Labels']),len(aa))):
                    responses['Labels'][i]['Name'] = aa[i].replace(' ','')
                    # print(aa[i])
               return self.create_response(responses)
          except Exception as error:
               print('[DEBUG]: {}'.format(error))
               error_code = error.response['Error']['Code']
               return self.make_response(500, '[FAILED]{}'.format(error))
     
     def check_validation(self, body: dict) -> Union[None, dict]:
          """
          バリデーションチェックをする関数
          """
          print('[DEBUG]check_validation()')
          if not body:
               return self.make_response(400, '[FAILED]Data required')
          if not isinstance(body, dict):
               return self.make_response(400, '[FAILED]Invalid body type')
          
          errors: list = []
          for key_info in self.required_keys:
               key_name: str = key_info['name']
               key_type: tuple = key_info['type']
               if not key_name in body.keys():
                    errors.append('key "{}" not found'.format(key_name))
               elif body[key_name] == '':
                    errors.append('no value found for "{}"'.format(key_name))
               elif type(body[key_name]) not in key_type:
                    errors.append('invalid value type: "{}"'.format(key_name))
          for key_info in self.optional_keys:
               key_name = key_info['name']
               key_type = key_info['type']
               if key_name in body.keys():
                    if type(body[key_name]) not in tuple(key_type):
                         errors.append('invalid value type: "{}"'.format(key_name))
          if errors:
               return self.make_response(400, '[FAILED]' + ', '.join(errors))
          else: 
               return None

     def load_json(self, str_json: str) -> Tuple[bool, dict]:
          """
          JSON文字列をPythonで処理できる形にする
          """
          print('[DEBUG]load_json()')
          if str_json is None:
               return False, self.make_response(400, '[FAILED]Data required')
          # Lambdaテスト時にdict型で入ってくるためif分岐
          if isinstance(str_json, str):
               try:
                    return True, json.loads(str_json)
               except json.JSONDecodeError:
                    print('[DEBUG]json decode error')
                    return False, self.make_response(400, '[FAILED]json decode error')
          else:
               return True, str_json

     def make_response(self, status_code: int, msg: str, payloads: dict = None) -> dict:
          """
          レスポンスを作成する
          """
          print('[DEBUG]make_response()')
          if payloads:
               body = json.dumps({'msg': msg, 'payloads': payloads})
          else:
               body = json.dumps({'msg': msg})
          return {
               'statusCode': status_code,
               'headers': {"Access-Control-Allow-Origin" : "*"},
               'body': body,
          }


#　初期化
detect_post = getLabels()

def lambda_handler(event, _) -> dict:
     """
     POSTをトリガーとして実行
     """
     try:
          # リクエストボディの中の文字列型JSONデータをPythonで扱える形に変換する
          result, body = detect_post.load_json(event['body'])
          if not result:
               return body
          # リクエストボディの中に必要なパラメータがあるかや型が合っているかをチェックする
          validation_errors = detect_post.check_validation(body)
          if validation_errors:
               return validation_errors
          # リクエストボディから送られた画像データをバイナリに変換しRekognitionが受け取れる形にする
          image_binary = detect_post.decode_base64_to_binary(body['image_base64str'])
          # 画像認識を行い、結果を返す
          detect_result = detect_post.detect_labels(image_binary, body['threshold'])
          return detect_result
     except Exception as error:
          print('[DEBUG]500:{}'.format(error))
          return detect_post.make_response(500, '[FAILED]An error occurred : {}'.format(error))