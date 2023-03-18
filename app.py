from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/result', methods=['GET','POST'])
def result():
    if request.method == 'POST':
        test = request.form.get('test')
        return render_template('result.html', test = test)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)