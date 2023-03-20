from flask import Flask, render_template, request, redirect, url_for, Blueprint
from aws_process import aws_process
import os
import openai

app = Flask(__name__, static_folder = './static/img')
app.register_blueprint(aws_process)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/result', methods=['GET','POST'])
def result():
    if request.method == 'POST':
        test = request.form.get('test')
        # file = request.files['img']
        # file.save(os.path.join('./static/img',file.filename))

        openai.api_key = "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"

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                # {"role": "system", "content": "間違った解答をして下さい"}, #※1後述
                {"role": "user", "content": "アルファベットの最初の文字を教えて下さい"}, #※1後述
            ]
        )
        aaa = response["choices"][0]["message"]["content"]
                
        return render_template('result.html', test = aaa)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)