from flask import Flask, render_template

app = Flask(__name__, template_folder='../frontend')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/create_account')
def create_account():
    return render_template('create_account.html')

@app.route('/game')
def game():
    return render_template('game.html')