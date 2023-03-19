from flask import Flask, render_template, request, redirect, url_for, Blueprint

aws_process = Blueprint('aws_process', __name__)

@aws_process.route("/test")
def test():
    return render_template('test.html')