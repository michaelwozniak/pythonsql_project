from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
import sqlite3
import os
from functools import wraps
import string
import random
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, TextField
from passlib.hash import sha256_crypt

app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    c = sqlite3.connect('databases/coreApp.db')
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
    c = sqlite3.connect('databases/coreApp.db')
    conn = c.cursor()
    cursor = conn.execute("Select * from CONTACT")
    return render_template('contact.html', texts=cursor)

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

@app.route("/signup", methods = ["GET","POST"])
def signup():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate() == True:
        username = form.username.data
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        if "@" not in email:
            flash("Wrong email adress, please correct it!","danger")
            return render_template("signup.html", form = form)
        password = sha256_crypt.encrypt(str(form.password.data))
        c = sqlite3.connect('databases/coreApp.db')
        conn = c.cursor()
        conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        tmp = conn.fetchall()
        conn.close()
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


class LoginForm(Form):
    email = StringField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])

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
            conn.close()
            password = data['password']
            if sha256_crypt.verify(password_tmp, password):
                session['logged_in'] = True
                session['email'] = email
                session["username"] = data['username']
                session["ID"] = data['ID']
                flash('You are logged in', 'success')
                return redirect(url_for('index'))
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
@logged_in_checker
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('index'))

@app.route("/profile")
@logged_in_checker
def profile():
    c = sqlite3.connect('databases/coreApp.db')
    conn = c.cursor()
    tmp = f"CREATE VIEW profile_view AS SELECT name, surname, username, register_date, company_name, field_of_research, phone_number,job_position FROM users as A LEFT JOIN users_additional_informations as B on B.ID = A.ID WHERE A.ID = {session.get('ID')}"
    conn.execute("DROP VIEW IF EXISTS profile_view")
    conn.execute(tmp)
    conn.execute("select* from view_name")
    conn.row_factory = sqlite3.Row 
    rows = conn.fetchall()
    data = dict(rows[0])
    conn.close()
    return render_template("profile.html", text=data)

class ProfileForm(Form):
    name = StringField('Name', [validators.Length(min=2, max=50)])
    surname = StringField('Surname', [validators.Length(min=2, max=50)])
    company_name = StringField('Company name', [validators.Length(min=2, max=100)])
    field_of_research = StringField('Field of research', [validators.Length(min=2, max=100)])
    phone_number = StringField('Phone number', [validators.Length(min=2, max=20)])
    job_position = StringField('Job position', [validators.Length(min=2, max=100)])

@app.route('/profile_edit', methods = ["GET","POST"])
@logged_in_checker
def profile_edit():
    form = ProfileForm(request.form)
    if request.method == 'POST' and form.validate() == True:
        name = form.name.data
        surname = form.surname.data
        company_name = form.company_name.data
        field_of_research = form.field_of_research.data
        phone_number = form.phone_number.data
        job_position = form.job_position.data
        c = sqlite3.connect('databases/coreApp.db')
        conn = c.cursor()
        conn.execute("UPDATE users SET name = ?, surname = ? WHERE ID = ?", (name,surname,session.get("ID"),))
        c.commit()
        conn = c.cursor()
        conn.execute("SELECT * FROM users_additional_informations WHERE ID = ?", (session.get("ID"),))
        tmp = conn.fetchall()
        if (len(tmp) != 0):
            conn = c.cursor()
            conn.execute("UPDATE users_additional_informations SET company_name = ?, field_of_research = ?, phone_number = ?, job_position = ? WHERE ID = ?", (company_name,field_of_research,phone_number,job_position, session.get("ID"),))
            c.commit()
            conn.close()
            return redirect(url_for('profile'))
        else:
            conn = c.cursor()
            conn.execute("INSERT INTO users_additional_informations (ID, company_name, field_of_research, phone_number , job_position) VALUES (?,?,?,?,?)", (session.get("ID"),company_name,field_of_research,phone_number,job_position,))
            c.commit()
            conn.close()
            return redirect(url_for('profile'))

    return render_template('profile_edit.html', form = form)


class CreatorForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    number_of_clusters = StringField('Number of clusters', [validators.Length(min=1)])
    comments = TextAreaField("Comments", [validators.Length(min=0)])

def id_generator(size=6, chars=string.ascii_uppercase + string.digits): 
    return ''.join(random.choice(chars) for _ in range(size))

@app.route("/creator",methods=["POST","GET"])
@logged_in_checker
def creator():
    form = CreatorForm(request.form)


    target = os.path.join(APP_ROOT, 'images/')
    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("file"):
        filename = id_generator(12) + ".png"
        destination = "/".join([target,filename])
        file.save(destination)

    return render_template('creator.html',form = form)


@app.route("/release")
@logged_in_checker
def release():
    return render_template('release.html')

if __name__ == ' __main__':
    app.secret_key = 'tomojsekretnyklucz123'
    app.run()

app.secret_key = 'tomojsekretnyklucz123'
app.run(port=5000, debug=True)
