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
# from threading import Thread
# import thread
import time
#from subprocess import Popen, PIPE
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
    print('index') 
    #send_email('monodualismus121212@gmail.com', 'hi', 'mail/test')
    return render_template('home.html')


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    print('submit a job')
    form = InputForm()
    if request.method == 'GET':
        # GET:
        return render_template('formular.html', form=form, tag_str="tag")

    print('post')

    f = request.files['pdb']
    if f.filename == '':
        f = request.files.get('dnd')
    atomRadii = request.form.get('options')
    tag = request.form['tag']
    email = request.form['email']
        
    print(tag)
        
    #Festlegen vom Pfad
    output_dir = '/disk/user_data/v4rna/sessions/'
    # output_dir = '/disk/user_data/v4rna/sessions/'
    #output_dir = '/home/hstudent/Desktop/voronoia/webapp/data/'
    if email != '' :
        output_dir += email + '/'
        if not os.path.exists( output_dir):
            os.mkdir(output_dir)
    else:
        output_dir += 'anonymous/'
        if not os.path.isdir( output_dir):
            os.mkdir(output_dir)
                
    #Zusammenfuegen des Directorynamens
    now = datetime.now()
    date = now.strftime("%Y%m%d%H%M")
    # random_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    #id_str = date + '_' + random_id +'/'
    id_str = date + '_' + tag + '/'
    output_dir += id_str
    print( output_dir)
    os.mkdir( output_dir)
        
    #Speichern der Datei 
    #filename = output_dir + secure_filename(f.filename)
    filename = output_dir + "protein.pdb" 
    f.save(filename) 
        
    #call main executable
    #process = Popen(["wine", "exec/get_volume.exe", "ex:0.1", "rad:protor" ,"i:" + filename + " o:" + filename[:-4] + ".vol"], stdout=PIPE, stderr=PIPE)
    #process = Popen(["python", "exec/test.py"], stdout=PIPE,stderr=PIPE)
    #cmd = "wine /home/hildilab/app/v4rna/exec/get_volume.exe ex:0.1 rad:protor i:%(data_pdb)s o:%(outputdir)s/%(BASE)s.vol >& %(BASE)s.log" % {"data_pdb": filename, "outputdir": "", "BASE": filename[:-4]}
     
    #call voronoia.py
    cmd = ["voronoia.py",filename , "-o", filename[:-4] + "_out","-vd"]
    print(cmd)
    # os.system(cmd)
    p = subprocess.check_output(cmd) #,stdout=subprocess.PIPE)
    print( p)
    # thread.start_new_thread( os.system , ( 'gedit ', ))
    print( "command terminated")
    


@app.route('/status/<user>/<job>')
def status( user, job):
    files_all_exist = True
    status = 'running'
    # check whether output files exist:
    # rather use walk, dirname is not job but date_job
    for name in ["protein.vol","protein.vol.extended.vol"]:
        fname = os.path.join( app.config['USER_DATA_DIR'] , user, job, name)
        if not os.path.isfile(fname):
            files_all_exist = False
            break
    if files_all_exist:
        status = 'finished'
    
    return jsonify( {'status':status} )  # returns dict 



@app.route('/downloads/<user>/<job>/<filename>')
def download( user, job, filename):
    path = app.config['USER_DATA_DIR'] + '/' + user + '/' + job
    print( "download:", path)
    return send_from_directory( path,filename)



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

    pdb_dir = ""
    for main, dirs, files in os.walk( os.path.join( app.config['USER_DATA_DIR'] , user )):
        for mdir in dirs:
            if tag in mdir:
                pdb_dir = mdir
                break
        if pdb_dir != "":
            break
    status_url = "/status/" + user + '/' + tag
    #dir = os.system("find ./ -name '*" + tag + "'") + "/"
    #pdb = dir + os.system("ls " + dir + " | grep .pdb")
    print("pdb name incoming")
    print(pdb_dir)
    return render_template('results.html', user=user, job=pdb_dir, status_url=status_url)



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
