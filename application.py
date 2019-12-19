from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
import sqlite3
from functools import wraps
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, TextField
from passlib.hash import sha256_crypt

app = Flask(__name__)

@app.route('/')
def index():
    c = sqlite3.connect('databases/content.db')
    conn = c.cursor()
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
    c = sqlite3.connect('databases/content.db')
    conn = c.cursor()
    cursor = conn.execute("Select * from CONTACT")
    return render_template('contact.html', texts=cursor)

@app.route("/signup", methods = ["GET","POST"])
def signup():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate() == True:
        username = form.username.data
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))
        c = sqlite3.connect('databases/coreApp.db')
        conn = c.cursor()
        conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        tmp = conn.fetchall()
        if (len(tmp)!=0):
            flash("Account with this email already exist! Please sign in!","danger")
            return render_template("signup.html", form = form)
        else:
            conn.execute('''INSERT INTO users(name, surname, email, username, password) VALUES(?,?,?,?,?)''', (name, surname, email, username, password))
            c.commit()
            c.close()
            flash('Signed up! Now, feel free to sign in :-)', 'success')
            return redirect(url_for('signup'))
    return render_template("signup.html", form = form)

@app.route("/signin", methods = ["GET","POST"])
def signin():
    form = LoginForm(request.form)
    if request.method == 'POST':
        email = form.email.data
        password_tmp = form.password.data
        c = sqlite3.connect('databases/coreApp.db')
        conn = c.cursor()
        conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        tmp = conn.fetchall()
        if (len(tmp) != 0):
            conn.execute("SELECT * FROM users WHERE email = ?", (email,))
            conn.row_factory = sqlite3.Row 
            rows = conn.fetchall()
            data = dict(rows[0])
            password = data['password']
            if sha256_crypt.verify(password_tmp, password):
                session['logged_in'] = True
                session['email'] = email
                session["username"] = data['username']
                flash('You are logged in', 'success')
                return redirect(url_for('panel'))
            else:
                error = 'Invalid login, try again!'
                return render_template('signin.html', error=error,form=form)
        else:
            error = 'Email not found'
            return render_template('signin.html', error=error,form=form)
    return render_template("signin.html",form=form)

def logged_in_checker(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized!, Please login now!', 'danger')
            return redirect(url_for('signin'))
    return wrap

@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('index'))

@app.route("/panel")
@logged_in_checker
def panel():
    return render_template('panel.html')


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

class LoginForm(Form):
    email = StringField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])


if __name__ == ' __main__':
    app.secret_key = 'tomojsekretnyklucz123'
    app.run()

app.secret_key = 'tomojsekretnyklucz123'
app.run(port=5000, debug=True)
