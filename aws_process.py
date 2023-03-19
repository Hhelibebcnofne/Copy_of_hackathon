from flask import Flask, render_template, request, redirect, url_for, Blueprint
import os

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