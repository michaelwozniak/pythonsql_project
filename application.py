from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
import sqlite3

app = Flask(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect('databases/content.db')
    cursor = conn.execute("Select * from HOME")
    return render_template('index.html',texts=cursor)

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/features_more')
def features_more():
    return render_template('features_more.html')

@app.route('/contact')
def contact():
    conn = sqlite3.connect('databases/content.db')
    cursor = conn.execute("Select * from CONTACT")
    return render_template('contact.html', texts=cursor)



if __name__ == ' __main__':
    app.run()

app.run(port=5000, debug=True)
