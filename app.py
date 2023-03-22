from flask import Flask, render_template, request, redirect, url_for, Blueprint
from aws_process import aws_process
import os
from dotenv import load_dotenv
import openai

app = Flask(__name__, static_folder = './static')
app.register_blueprint(aws_process)
load_dotenv()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/result', methods=['GET','POST'])
def result():
    if request.method == 'POST':
        test = request.form.get('test')
        li = test.split("、")
        # print(li)
        question = ""
        for s in li:
            question += s + "、"
        else:
            question += "の単語を繋げていけてる感じでインスタに投稿する文章を考えて"
        print(question)
        
        # file = request.files['img']
        # file.save(os.path.join('./static/img',file.filename))

        openai.api_key = os.environ['OPEN_AI_KEY']

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                # {"role": "system", "content": "間違った解答をして下さい"}, #※1後述
                {"role": "user", "content": question}, #※1後述
            ]
        )
        aaa = response["choices"][0]["message"]["content"]
                
        return render_template('result.html', test = aaa)
        # return render_template('result.html')
    else:
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