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
import threading

import sqlite3 as sql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Lhvz7/{{4$34"_.b'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SENDER'] = 'PROFESSIONAL TESTER <monodualist121212@gmail.com>'
app.config['USER_DATA_DIR'] = "/disk/user_data/voronoia/sessions/"
app.config['APP_PATH'] = "/home/hildilab/app/voronoia/"

bootstrap = Bootstrap(app)

mail = Mail(app)

sql_db = "/disk/data/voronoia/jobs.db"


class InputForm(FlaskForm):
    # creation of input fields
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


def execute_cmd(cmd):
    P = subprocess.check_output(cmd)


def calculation(filename, output_dir):
    # call voronoia.py
    execute_cmd(["voronoia.py",filename , "-o", output_dir,"-vd"])
    # call get_holes.py
    execute_cmd([app.config['APP_PATH'] + "get_holes.py", output_dir,"protein.vol.extended.vol"])
    # create zip file
    os.chdir(output_dir)
    execute_cmd(["zip", "results.zip", "onlyHoles.pdb", "protein.vol.extended.vol", "selection"])


def start_thread(function, args, name):
    t = threading.Thread(target=function, name=name, args=args)
    t.deamon = True
    t.start()


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = InputForm()
    if request.method == 'GET':
        return render_template('formular.html', form=form, tag_str="tag")

    f = request.files['pdb']
    if f.filename == '':
        f = request.files.get('dnd')
    atomRadii = request.form.get('options')
    tag = request.form['tag']
    email = request.form['email']
        
    # create path
    output_dir = app.config['USER_DATA_DIR']
    if email != '' :
        email = 'anonymous'
    output_dir += email + '/'
    if not os.path.exists( output_dir):
        os.mkdir(output_dir)
    output_dir += tag + '/'
    os.mkdir(output_dir)
        
    # save file
    filename = output_dir + "protein.pdb" 
    f.save(filename) 

    start_thread(calculation, [filename, output_dir], 'zip')

    print('command terminated')
    return redirect(url_for('wait', user=email, job=tag))


@app.route('/status/<user>/<job>')
def status(user, job):
    # returns info about the status of the calculation
    status = 'running'
    fname = os.path.join(app.config['USER_DATA_DIR'], user, job, "onlyHoles.pdb")
    print("exists?: ",fname,job)
    if os.path.isfile(fname):
        status = 'finished'
        print('yes')

    return jsonify({'status':status,'error':'0'}) 


@app.route('/progress/<user>/<job>')
def wait(user, job):
    return render_template('wait.html', user=user, job=job)


#@app.route('/lic/<user>/<job>')
def get_lic_selection(user, job):
    filename = app.config['USER_DATA_DIR'] + user + '/' + job + '/selection'
    return open(filename, 'r').read().replace('\n', '').replace('\r', '')


@app.route('/results/<user>/<job>')
def results(user, job):
    return render_template('results.html', user=user, job=job, lic_selection=get_lic_selection(user, job))


@app.route('/menu')
def menu():
    user = 'anonymous'
    job = 'hurray'
    return render_template('menu.html', user=user, job=job)


@app.route('/downloads/<user>/<job>/<filename>')
def download( user, job, filename):
    path = app.config['USER_DATA_DIR'] + '/' + user + '/' + job 
    print( "download:", path)
    return send_from_directory( path,filename)

"""
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
"""


@app.route('/databank')
def databank():
    con = sql.connect(sql_db)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM jobs")
    con.commit()
    rows = cur.fetchall()
    con.close()
    return render_template('databank.html', rows = rows)


@app.route('/db-results/<pdb>')
def dbresults(pdb):
    return render_template('references.html')


@app.route('/methods')
def methods():
    return render_template('methods.html')


@app.route('/references')
def references():
    return render_template('references.html')

