from flask import Flask, render_template, request, redirect, url_for, Blueprint
from aws_process import aws_process
import os
from dotenv import load_dotenv
import openai

app = Flask(__name__, static_folder = './static')
app.register_blueprint(aws_process)
load_dotenv()
OPEN_AI_KEY = "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"

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/service')
def service():
    return render_template('service.html')

# @app.route('/gpt', methods=['GET','POST'])
# def gpt():
#     if request.method == 'POST':
#         people_li = request.form.get('people').split("、")
#         place = request.form.get('place')
#         lable_li = request.form.get('label').split("、")
#         question = ""
#         is_people = False
#         is_place = False
        
#         if people_li[0] != '':
#             is_people = True
#             question += "人物："
#             for i in range(len(people_li)):
#                 if i == len(people_li) - 1:
#                     question += f'{people_li[i]}\n'
#                 else:
#                     question += f'{people_li[i]}、'
        
#         if len(place) != 0:
#             is_place = True
#             question += f'場所：{place}\n'
            
#         question += 'ラベル：'
#         for i in range(len(lable_li)):
#             if i == len(lable_li) - 1:
#                 question += f'{lable_li[i]}\n'
#             else:
#                 question += f'{lable_li[i]}、'
        
            
#         if is_people and is_place:
#             question += "場所と人物は全て、ラベルは必要なものだけを使って、インスタに投稿するための文章を日本語で考えて"
#         elif is_people:
#             question += "人物は絶対全て、ラベルは必要なものだけを使って、インスタに投稿するための文章を日本語で考えて"
#         elif is_place:
#             question += "場所は絶対、ラベルは必要なものだけを使って、インスタに投稿するための文章を日本語で考えて"
#         else:
#             question += "ラベルは必要なものだけを使って、インスタに投稿するための文章を日本語で考えて"
            
#         print(question)

#         openai.api_key = os.environ['OPEN_AI_KEY']

#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 # {"role": "system", "content": "間違った解答をして下さい"}, #※1後述
#                 {"role": "user", "content": question}, #※1後述
#             ]
#         )
#         aaa = response["choices"][0]["message"]["content"]
#         li = [people_li,place,aaa]
                
#         return render_template('gpt.html',li = li)
#     else:
#         return render_template('index.html')
    
@app.route('/images', methods=['GET','POST'])
def images():
    if request.method == 'POST':
        files = request.files.getlist('images')
        for file in files:
            print(file.filename)
        print("-------------------------")
        return render_template('index.html')

# @aws_process.route("/test", methods=['GET', 'POST'])
# def test():
#     if request.method == 'POST':
#         test = request.form.get('test')
#         file = request.files['img']
#         file.save(os.path.join('./static/img',file.filename))
#         return render_template('test.html', test = file.filename)
#     else:
#         return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)