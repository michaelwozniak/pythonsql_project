from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
import sqlite3
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

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

@app.route("/sign", methods = ["GET","POST"])
def signup():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate() == True:
        username = form.username.data
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        conn = sqlite3.connect('databases/coreApp.db')
        conn.execute('''INSERT INTO users(name, surname, email, username, password) VALUES(?,?,?,?,?)''', (name, surname, email, username, password))
        conn.commit()
        conn.close()
        flash('Signed up! Now, please sign in!', 'success')
        return redirect(url_for('signup'))
    return render_template("sign.html", form = form)

@app.route("/sign", methods = ["GET","POST"])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password_try = request.form['password']
        conn = sqlite3.connect('databases/coreApp.db')
        result = conn.execute("SELECT * FROM users WHERE username = ?", [email])
         if (result != 0):
             data = conn.fetchone()



    return render_template("sign.html")



class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=5, max=25)])
    name = StringField('Name', [validators.Length(min=2, max=50)])
    surname = StringField('Surname', [validators.Length(min=2, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Wrong password')
    ])
    confirm = PasswordField('Confirm password')

if __name__ == ' __main__':
    app.secret_key = 'tomojsekretnyklucz123'
    app.run()

app.secret_key = 'tomojsekretnyklucz123'
app.run(port=5000, debug=True)
