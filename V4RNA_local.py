from flask import Flask, render_template, session, url_for, redirect, request
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
from threading import Thread
import time
from subprocess import Popen, PIPE
import subprocess

import sqlite3 as sql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Lhvz7/{{4$34"_.b'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['FLASKY_MAIL_SENDER'] = 'PROFESSIONAL TESTER <monodualist121212@gmail.com>'


bootstrap = Bootstrap(app)

mail = Mail(app)

sql_db = "jobs.db"


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
    if request.method == 'POST':
        print('post')
        #print( getpass.getuser())
        #print(os.getcwd())

        #EINLESEN
        f = request.files['pdb']
        if f.filename == '':
            f = request.files.get('dnd')
        atomRadii = request.form.get('options')
        tag = request.form['tag']
        email = request.form['email']
        
        
        
        
        
        
        #Festlegen vom Pfad
        #output_dir = '/disk/user_data/v4rna/sessions/'
        output_dir = '/home/hstudent/Desktop/voronoia/webapp/data/'
        if email != '':
            output_dir += email + '/'
            os.mkdir(output_dir)
        else:
            output_dir += 'anonymous/'
            if not os.path.isdir( output_dir):
                os.mkdir(output_dir)
                
        #Zusammenfügen des Directorynamens
        now = datetime.now()
        date = now.strftime("%Y%m%d%H%M")
        random_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        id_str = date + '_' + random_id +'/'
        output_dir += id_str
        print( output_dir)
        os.mkdir( output_dir)
        
        #Speichern der Datei 
        filename = output_dir + secure_filename(f.filename)
        f.save(filename) 
        
        #call main executable
        #process = Popen(["wine", "exec/get_volume.exe ex:0.1 rad:protor i:" + filename + " o:" + filename[:-4] + ".vol"], stdout=PIPE, stderr=PIPE)
        #process = Popen(["python", "exec/test.py"], stdout=PIPE,stderr=PIPE)
        
        #cmd = "wine exec/get_volume.exe ex:0.1 rad:protor i:" + filename + " o:" + filename[:-4] + ".vol"
        
        #print(stdout)
#        print(cmd)
#        os.system(cmd)
        
        #call voronoia.py
#        cmd = "voronoia.py " + filename + " -o " + filename[:-4] + ".tmp -vd"
#        print(cmd)
#        os.system(cmd)
        
        
        #return redirect('/status') # uebergabe pfad an ausgabe seite
        print("test")
        return {'Location': url_for('status'), 'tag':tag}
        #return redirect('methods', code=278)
        #return render_template('formular.html', form=form, tag_str="tag")
        #return redirect(url_for('methods'))
        #return redirect('methods', code=278)
        #return redirect('methods', code=302)
        #return redirect(url_for('methods'))
        #print(url_for('methods'))
        #return redirect(url_for('methods'))
        #return render_template( "formular.html",form=form ,tag_str=tag )
        #print("check")
    return render_template('formular.html', form=form, tag_str="tag")

@app.route('/status')
def status():
    return render_template('status.html')

@app.route('/results')
def result():
    tag = request.url.split('=')[-1]
    con = sql.connect(sql_db)
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT pdb FROM jobs WHERE tag = '" + tag + "'")
    rows = cur.fetchall()
    pdb = rows[0]['pdb']
    con.close()
    return render_template('results.html', pdb=pdb, tag=tag)

@app.route('/databank')
def databank():
    con = sql.connect(sql_db)
    con.row_factory = sql.Row
    cur = con.cursor()
    ranStr = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    ranTag = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(2))
    cur.execute("INSERT INTO jobs (id,tag,pdb,vol) VALUES (?,?,?,?)" , ("1",ranTag,ranStr + ".pdb",ranStr + ".vol") )
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
