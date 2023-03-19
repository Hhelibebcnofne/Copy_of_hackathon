from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__, static_folder = './static/img')

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/result', methods=['GET','POST'])
def result():
    if request.method == 'POST':
        test = request.form.get('test')
        file = request.files['img']
        file.save(os.path.join('./static/img',file.filename))
        return render_template('result.html', test = file.filename)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)