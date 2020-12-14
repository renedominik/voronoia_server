from flask import Flask, render_template, session, url_for, redirect, request, send_from_directory, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import  StringField, SubmitField, SelectField, FileField
from wtforms.validators import Email, DataRequired
from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage

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
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
#app.config['MAIL_USERNAME'] = 'monodualismus121212@gmail.com'
app.config['MAIL_DEFAULT_SENDER'] = 'hildilab@proteinformatics.uni-leipzig.de'
#app.config['MAIL_PASSWORD'] = 'monoduo12'
app.config['USER_DATA_DIR'] = "/disk/user_data/voronoia/sessions/"
# app.config['DATABASE_DIR'] = "/home/hildilab/app/voronoia/static/archive/"
app.config['DATABASE_DIR'] = "/disk/data/voronoia/data/"
app.config['EXAMPLES_DIR'] = "/home/hildilab/app/voronoia/static/examples/"
app.config['APP_PATH'] = "/home/hildilab/app/voronoia/"

bootstrap = Bootstrap(app)

mail = Mail(app)

sql_db = "/disk/data/voronoia/db.sql"

example_pdb = '1lib.pdb'


class InputForm(FlaskForm):
    # creation of input fields
    pdb = FileField('Upload a pdb file:')#, validators=[FileRequired()])
    email = StringField('Email*:', validators=[Email()])
    tag = StringField('Tag:', validators=[DataRequired()]) 
    submit = SubmitField('Analyse')

    def validate(self):
        print(self.pdb)
        fn = secure_filename(self.pdb.data.filename)
        print("validate:",fn)
        return '.' in fn and (fn.rsplit('.', 1)[-1] == 'pdb')


def send_email(to, subject, template):
    print('sending email')
    print('to: ' + to)
    print('saying: ' + template)
    msg = Message(subject, recipients=[to])
    msg.body = template
    mail.send(msg)


@app.route('/')
def index():
    return render_template('home.html')


def execute_cmd(cmd):
    p = subprocess.check_output(cmd)


def calculation(filename, output_dir, email, job):
    # call voronoia.py
    execute_cmd(["voronoia.py",filename , "-o", output_dir,"-vd"])
    # call get_holes.py
    execute_cmd([app.config['APP_PATH'] + "get_holes.py", output_dir,"protein.vol.extended.vol"])
    # create zip file
    os.chdir(output_dir)
    execute_cmd(["zip", "results.zip", "onlyHoles.pdb", "protein.vol.extended.vol", "selection"])
    # optionally send email
    if email != 'anonymous':
        #with app.app_context():
        with app.app_context(), app.test_request_context():
            results_link = url_for('results', user=email, job=job)
            send_email(email, 'Voronoia', 'Your calculation is done. You can view your results under: http://www.proteinformatics.de/voronoia' + results_link)


def start_thread(function, args, name):
    t = threading.Thread(target=function, name=name, args=args)
    t.deamon = True
    t.start()


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = InputForm()
    if request.method == 'GET':
        return render_template('submit.html', form=form, tag_str="tag", example_pdb=example_pdb)

    print(request.files)

    f = request.files['pdb']
    if f.filename == '':
        f = request.files.get('dnd')
    if f is None:
        # we assume that if neither the button nor the drag and drop box was used, the user must have loaded the example
        f = FileStorage(open(app.config['EXAMPLES_DIR'] + example_pdb, 'rb'))

    print(f)
    print(type(f))

    # atomRadii = request.form.get('options')
    tag = request.form['tag']
    email = request.form['email']
        
    # create path
    output_dir = app.config['USER_DATA_DIR']
    #if email == '' :
        #email = 'anonymous'
    output_dir += email + '/'
    if not os.path.exists( output_dir):
        os.mkdir(output_dir)
    output_dir += tag + '/'

    try:
        os.mkdir(output_dir)
    except:
        # tag has already been used
        return render_template('submit.html', form=form, tag_str="tag", example_pdb=example_pdb)
        
    # save file
    filename = output_dir + "protein.pdb" 
    f.save(filename) 

    start_thread(calculation, [filename, output_dir, email, tag], 'zip')

    print('command terminated')
    return redirect(url_for('progress', user=email, job=tag))


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


@app.route('/example')
def load_example():
    return send_from_directory(app.config['EXAMPLES_DIR'], example_pdb)


@app.route('/progress/<user>/<job>')
def progress(user, job):
    return render_template('progress.html', user=user, job=job)


def get_lic_selection(user, job):
    filename = app.config['USER_DATA_DIR'] + user + '/' + job + '/selection'
    return open(filename, 'r').read().replace('\n', '').replace('\r', '')


def get_db_lic_selection(pdb):
    filename = app.config['DATABASE_DIR'] + pdb + '/selection'
    return open(filename, 'r').read().replace('\n', '').replace('\r', '')


@app.route('/results/<user>/<job>')
def results(user, job):
    f = os.path.join(app.config['USER_DATA_DIR'], user, job, "onlyHoles.pdb")
    if os.path.isfile(f):
        return render_template('results.html', user=user, job=job, lic_selection=get_lic_selection(user, job))
    return redirect(url_for('progress', user=user, job=job))


@app.route('/db-results/<pdb>')
def db_results(pdb):
    #return render_template('db_results.html', pdb=pdb, lic_selection=get_db_lic_selection(pdb))
    return render_template('db_results.html', pdb=pdb)


@app.route('/menu')
def menu():
    return render_template('menu.html')


@app.route('/db-menu')
def db_menu():
    return render_template('db_menu.html')


@app.route('/downloads/<user>/<job>/<filename>')
def download( user, job, filename):
    path = app.config['USER_DATA_DIR'] + '/' + user + '/' + job 
    return send_from_directory(path,filename)


@app.route('/db-downloads/<pdb>/<filename>')
def db_download(pdb, filename):
    path = app.config['DATABASE_DIR'] + '/'
    return send_from_directory(path, pdb + filename)


@app.route('/database', methods=['GET', 'POST'])
def database():
    """
    con = sql.connect(sql_db)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT pdbid, title FROM content")
    con.commit()
    rows = cur.fetchall()
    con.close()
    return render_template('database.html', rows = rows)
    """
    if request.method == 'GET':
        return render_template('database.html')
    id = request.form['pdb-id'].lower()
    return redirect(url_for('db_results', pdb=id))


@app.route('/methods')
def methods():
    return render_template('methods.html')


@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')


@app.route('/sendmail')
def m():
    send_email("monodualismus121212@gmail.com", "hi", "template")

if __name__ == '__main__':
    app.run(ssl_context= ('/etc/apache2/ssl/cert-11043954791332636805298309362.pem', '/etc/apache2/ssl/key.pem' ))
