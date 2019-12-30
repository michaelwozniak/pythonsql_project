from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_from_directory
from functools import wraps
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, TextField, DecimalField
from passlib.hash import sha256_crypt
import sqlite3
import os
import pandas as pd
import numpy as np
import time
import string
import random
import shutil
from model import Model
import tensorflow as tf
from keras.applications.inception_resnet_v2 import InceptionResNetV2

global graph
graph = tf.get_default_graph()
model = InceptionResNetV2(weights='imagenet', include_top=False, classes=1000) 

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
    tmp = f"CREATE VIEW profile_view AS SELECT name, surname, username, register_date, company_name, field_of_research, \
        phone_number,job_position FROM users as A LEFT JOIN users_additional_informations as B on B.ID = A.ID WHERE A.ID = {session.get('ID')}"
    conn.execute("DROP VIEW IF EXISTS profile_view")
    conn.execute(tmp)
    conn.execute("select* from profile_view")
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
    phone_number = StringField('Phone number', [validators.Length(min=0, max=20)])
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
    number_of_clusters = DecimalField('Number of clusters', [validators.NumberRange(min=2, max=10, message=' - number of classes must be in range from 2 to 10')])
    comments = TextAreaField("Comments", [validators.Length(min=0)])

def id_generator(size=6, chars=string.ascii_uppercase + string.digits): 
    return ''.join(random.choice(chars) for _ in range(size))

@app.route("/creator",methods=["POST","GET"])
@logged_in_checker
def creator():
    form = CreatorForm(request.form)
    if request.method == 'POST' and form.validate() == True:
        title = form.title.data
        number_of_clusters = str(form.number_of_clusters.data)
        comments = form.comments.data
        c = sqlite3.connect('databases/coreApp.db')
        conn = c.cursor()
        hash_gen = id_generator(40)
        conn.execute("INSERT INTO projects(user_ID,hash) VALUES (?,?)", (session.get("ID"),hash_gen))
        c.commit()
        conn.execute("select * from projects WHERE user_ID = ? ORDER BY ID DESC LIMIT 1;", (session.get("ID"),))
        conn.row_factory = sqlite3.Row 
        rows = conn.fetchall()
        data = dict(rows[0])
        project_id = data["ID"]
        conn = c.cursor()
        conn.execute("INSERT INTO projects_settings(ID, title, number_of_clusters, comments) VALUES (?,?,?,?)", (project_id,title,number_of_clusters,comments))
        c.commit()
        c.close()
        return redirect(url_for('creator_img'))
    return render_template('creator.html',form = form)

@app.route("/creator_img",methods=["POST","GET"])
@logged_in_checker
def creator_img():
    target = 'static/images/input/'
    if not os.path.isdir(target):
        os.mkdir(target)

    controller = 0
    for file in request.files.getlist("file"):
        filename = file.filename
        ext = os.path.splitext(filename)[1]
        if (ext == ".png"):
            destination = "/".join([target,filename])
            file.save(destination)
            foo_name = id_generator(20) + '.png'
            foo_destination = "/".join([target,foo_name])
            os.rename(destination,foo_destination)
            controller = controller + 1
            c = sqlite3.connect('databases/coreApp.db')
            conn = c.cursor()
            conn.execute("select * from projects WHERE user_ID = ? ORDER BY ID DESC LIMIT 1;", (session.get("ID"),))
            conn.row_factory = sqlite3.Row 
            rows = conn.fetchall()
            data = dict(rows[0])
            project_id = data["ID"]
            c = sqlite3.connect('databases/coreApp.db')
            conn = c.cursor()
            conn.execute("INSERT INTO images(img_name, project_ID) VALUES (?,?)", (foo_destination,project_id,))
            c.commit()
            c.close()

    if controller != 0:
        time.sleep(2)
        task = f"create view images_to_model as select img_name from images WHERE project_id = {project_id}"
        c = sqlite3.connect('databases/coreApp.db')
        conn = c.cursor()
        conn.execute("DROP VIEW IF EXISTS images_to_model")
        conn.execute(task)
        conn.execute("select * from images_to_model")
        rows = conn.fetchall()
        files_list = list()
        for i in rows:
            files_list.append(i[0])

        conn = c.cursor()
        conn.execute("SELECT number_of_clusters FROM projects_settings WHERE ID = ?", (project_id,))
        conn.row_factory = sqlite3.Row 
        rows = conn.fetchall()
        data = dict(rows[0])
        number_of_clusters = int(data["number_of_clusters"])
        try:
            with graph.as_default():
                cnn_birch_model = Model(files_list,number_of_clusters,model)
                cnn_birch_model.preprocessing_images_and_model_loading()
                cnn_birch_model.model_application()
                cnn_birch_model.pca_plot()
                cnn_birch_model.sillhouette_plot()
                labels = cnn_birch_model.birch_model_and_plot()
            conn = c.cursor()
            conn.execute("SELECT ID FROM images WHERE project_id = ?", (project_id,))
            rows = conn.fetchall()
            img_tmp = list()
            for i in rows:
                img_tmp.append(i[0])

            for i in range(len(labels)):
                conn = c.cursor()
                conn.execute("INSERT INTO images_clusters(ID, clusters) VALUES (?,?)", (img_tmp[i],int(labels[i]),))
                c.commit()

            conn = c.cursor()
            conn.execute("INSERT INTO extra_plots(plot1_name, plot2_name, plot3_name, project_ID) VALUES (?,?, ?,?)", (cnn_birch_model.sillhouette_name,cnn_birch_model.pca_name,cnn_birch_model.birch_name,project_id))
            c.commit()

            flash("Computations completed!","success")
            time.sleep(2)
            return redirect(url_for('release'))
        except:
            flash("Something went wrong, please try again!","danger")
            redirect(url_for("creator"))
    
    return render_template('creator_img.html')

@app.route("/release")
@logged_in_checker
def release():
    c = sqlite3.connect('databases/coreApp.db')
    conn = c.cursor()
    command = f"CREATE VIEW dashboard as SELECT title, number_of_clusters, create_date, COUNT(c.ID) as number_of_images,\
         hash FROM projects_settings AS a LEFT JOIN projects as b ON a.ID = b.ID LEFT JOIN images as c ON a.ID = c.project_id\
              LEFT JOIN extra_plots as d ON a.ID = d.project_ID WHERE user_id = {session.get('ID')} AND d.project_ID IS\
                   NOT NULL GROUP BY c.project_id ORDER BY create_date"    
    conn.execute("DROP VIEW IF EXISTS dashboard")
    conn.execute(command)
    conn.execute("SELECT * from dashboard")
    conn.row_factory = sqlite3.Row 
    rows = conn.fetchall()
    data = [dict(i) for i in rows]
    if len(data) > 0:
        return render_template('release.html', data=data)
    else:
        msg = 'Empty! Create some projects!'
        return render_template('release.html', msg=msg)
    conn.close()

@app.route('/case/<string:hash_id>/')
@logged_in_checker
def case(hash_id):
    c = sqlite3.connect('databases/coreApp.db')
    conn = c.cursor()
    conn.execute("SELECT name, surname, email, company_name, field_of_research, phone_number, job_position,\
         title, number_of_clusters,comments,create_date, plot1_name, plot2_name, plot3_name, clusters , \
             count(name) as number_of_images FROM users LEFT JOIN users_additional_informations ON \
                 users.ID = users_additional_informations.ID LEFT JOIN projects ON users.ID = projects.user_ID LEFT JOIN projects_settings\
                      ON  projects_settings.ID = projects.ID LEFT JOIN extra_plots ON extra_plots.project_ID = projects.ID \
                          LEFT JOIN images ON projects_settings.ID = images.project_ID LEFT JOIN images_clusters ON \
                              images.ID = images_clusters.ID  WHERE hash = ? GROUP BY plot1_name,clusters", [hash_id])
    conn.row_factory = sqlite3.Row 
    rows = conn.fetchall()
    data = [dict(i) for i in rows]
    _ , data[0]["plot1_name"] = data[0]["plot1_name"].split("images/output/")
    _ , data[0]["plot2_name"] = data[0]["plot2_name"].split("images/output/")
    _ , data[0]["plot3_name"] = data[0]["plot3_name"].split("images/output/")
    
    directory_main_zip = 'static/images/download/'+str(hash_id)+".zip"
    if not os.path.exists(directory_main_zip):
        directory = 'static/images/download/'+str(hash_id)

        if not os.path.exists(directory):
            os.makedirs(directory)

        conn = c.cursor()
        conn.execute("SELECT img_name, clusters FROM images LEFT JOIN images_clusters ON images.ID = images_clusters.ID \
            LEFT JOIN projects ON images.project_ID = projects.ID WHERE hash = ?",[hash_id])
        conn.row_factory = sqlite3.Row 
        rows = conn.fetchall()
        df = [dict(i) for i in rows]
        df = pd.DataFrame(df)

        for i in df.clusters.unique():
            directory_clusters = 'static/images/download/'+str(hash_id)+'/'+str(i)
            if not os.path.exists(directory_clusters):
                os.makedirs(directory_clusters)

        for i in range(len(df)):
            _, name = df.iloc[i,1].split("//")
            directory_photos_clusters = 'static/images/download/'+str(hash_id)+'/'+str(df.iloc[i,0])+'/'+name
            if not os.path.exists(directory_photos_clusters):
                shutil.copy(df.iloc[i,1], directory_photos_clusters)

        directory_zip = "static/images/download/" + str(hash_id)
        output_file_zip = "static/images/download/" + str(hash_id)
        if not os.path.exists(f'{directory_zip}.zip'):
            shutil.make_archive(output_file_zip, 'zip', directory_zip)

        shutil.rmtree(directory_zip)
    to_dict = "static/images/download/" + str(hash_id)+".zip"
    data[0].update({"project_id_hash":to_dict})

    return render_template('case.html', case=data)

MEDIA_FOLDER_1 = os.path.join(APP_ROOT, 'static/images/output/')
@app.route('/uploads/<path:filename>')
@logged_in_checker
def display_img(filename):
    return send_from_directory(MEDIA_FOLDER_1, filename, as_attachment=True)


MEDIA_FOLDER_2 = os.path.join(APP_ROOT, 'static/images/download/')
@app.route('/<path:filename>')
@logged_in_checker
def download_files(filename):
    return send_from_directory(MEDIA_FOLDER_2, filename, as_attachment=True)


if __name__ == ' __main__':
    app.secret_key = 'tomojsekretnyklucz123'
    app.run(threaded=True)

app.secret_key = 'tomojsekretnyklucz123'
app.run(port=5000, debug=True,threaded=True)
