from flask import Flask, render_template, session, url_for, redirect, request, send_from_directory, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_mail import Mail
from flask_mail import Message
from wtforms import  StringField, SubmitField, SelectField, FileField
from wtforms.validators import Email, DataRequired
from werkzeug import secure_filename

from datetime import datetime
import random, string, os
import getpass
import time
import subprocess

import sqlite3 as sql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Lhvz7/{{4$34"_.b'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SENDER'] = 'PROFESSIONAL TESTER <monodualist121212@gmail.com>'
app.config['USER_DATA_DIR'] = "/disk/user_data/v4rna/sessions/"
app.config['APP_PATH'] = "/home/hildilab/app/v4rna/"

bootstrap = Bootstrap(app)

mail = Mail(app)

sql_db = "/disk/data/v4rna/jobs.db"


class InputForm(FlaskForm):
    #Definieren der Eingabefelder
    pdb = FileField('Upload a pdb file:')#, validators=[FileRequired()])
    email = StringField('Email*:', validators=[Email()])
    tag = StringField('Tag:', validators=[DataRequired()])
    options = SelectField('Atom radii:', choices=[('1', 'ProtOr'), ('2', 'Stouten')])    
    submit = SubmitField('Analyse')

    def validate(self):
        print(self.pdb)
        fn = secure_filename(self.pdb.data.filename)
        print("validate:",fn)
        return '.' in fn and (fn.rsplit('.', 1)[-1] == 'pdb')

    
def send_email(to, subject, template, **kwargs):
    print('hi')
    msg = Message(subject, sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    mail.send(msg)


@app.route('/')
def index():
    # TODO: add mail notification
    return render_template('home.html')


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = InputForm()
    if request.method == 'GET':
        return render_template('formular.html', form=form, tag_str="tag")

    print('post')

    f = request.files['pdb']
    if f.filename == '':
        f = request.files.get('dnd')
    atomRadii = request.form.get('options')
    tag = request.form['tag']
    email = request.form['email']
        
    #Festlegen vom Pfad
    output_dir = '/disk/user_data/v4rna/sessions/'

    if email != '' :
        email = 'anonymous'
    output_dir += email + '/'
    if not os.path.exists( output_dir):
        os.mkdir(output_dir)
                
    output_dir += tag + '/'
    print( output_dir)
    os.mkdir( output_dir)
        
    #Speichern der Datei 
    filename = output_dir + "protein.pdb" 
    f.save(filename) 
        
    #call voronoia.py
    cmd = ["voronoia.py",filename , "-o", output_dir,"-vd"]
    print(cmd)
    p = subprocess.check_output(cmd) 
    print( p)
    cmd = [ app.config['APP_PATH'] + "get_holes.py", output_dir,"protein.vol.extended.vol"]
    print(cmd)
    p = subprocess.check_output(cmd) 
    print( p)
    print( "command terminated")

    status_url = "/status/" + email + "/" + tag

    return render_template("results.html", user=email, job=tag, lic_selection="ABBA")


@app.route('/status/<user>/<job>')
def status( user, job):
    status = 'running'
    fname = os.path.join( app.config['USER_DATA_DIR'] , user, job, "onlyHoles.pdb")
    print("exists?: ",fname,job)
    if os.path.isfile(fname):
        status = 'finished'
        print('yes')
     
    return jsonify( {'status':status,'error':'0'} )  # returns dict 



@app.route('/downloads/<user>/<job>/<filename>')
def download( user, job, filename):
    path = app.config['USER_DATA_DIR'] + '/' + user + '/' + job 
    print( "download:", path)
    return send_from_directory( path,filename)



#@app.route('/textdownloads/<user>/<job>/<filename>')
#def text_download(user, job, filename):
    #path = app.config['USER_DATA_DIR'] + '/' + user + '/' + job
    #return jsonify({'selection':


@app.route('/results/<user>/<tag>')
def result(user, tag):
    # check first if the tag is in the db:
    #tag = request.url.split('=')[-1]
    #con = sql.connect(sql_db)
    #con.row_factory = sql.Row
    #cur = con.cursor()
    #cur.execute("SELECT pdb FROM jobs WHERE tag = '" + tag + "'")
    #rows = cur.fetchall()
    #pdb = rows[0]['pdb']
    #con.close()
    # if not, check the user data:

    status_url = "/status/" + user + "/" + tag
    
    return render_template('results.html', user=user, job=tag, status_url=status_url)


@app.route('/databank')
def databank():
    print('i am alive and well')
    print(sql_db)
    con = sql.connect(sql_db)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM jobs")
    con.commit()
    rows = cur.fetchall()
    con.close()
    return render_template('databank.html', rows = rows)



@app.route('/methods')
def methods():
    return render_template('methods.html')



@app.route('/references')
def references():
    return render_template('references.html')


def find_job(user, tag):
    pdb_dir = ""
    for mdir in os.listdir( os.path.join( app.config['USER_DATA_DIR'] , user )):
        if os.path.isdir(mdir):
            if tag in mdir:
                pdb_dir = mdir
                break
        if pdb_dir != "":
            break
    return pdb_dir
