from flask import Flask, render_template, session, url_for, redirect, request, send_from_directory, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import  StringField, SubmitField, SelectField, FileField, BooleanField
from wtforms.validators import Email, DataRequired
from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage

from datetime import datetime
import random, string, os
import getpass
import time
import subprocess
import threading
from zipfile import ZipFile

#import sqlite3 as sql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Lhvz7/{{4$34"_.b'
app.config['USER_DATA_DIR'] = "/disk/user_data/voronoia/sessions/"
# app.config['DATABASE_DIR'] = "/home/hildilab/app/voronoia/static/archive/"
app.config['DATABASE_DIR'] = "/disk/data/voronoia/data/"
app.config['EXAMPLES_DIR'] = "/home/hildilab/app/voronoia/static/examples/"
app.config['APP_PATH'] = "/home/hildilab/app/voronoia/"
app.config['SCRIPTS_PATH'] = "/home/hildilab/app/voronoia/material/"

bootstrap = Bootstrap(app)

#sql_db = "/disk/data/voronoia/db.sql"

example_pdb = '1lib.pdb'

# wird nicht genutzt, da javascript testet bevor dies aufgerufen wird!
def check_ending(form,field):
    if field.data:
        ext = os.path.splitext( field.data.filename)[1].strip('.').lower()
        if ext != '.pdb' and ext != '.zip':
            raise validators.ValidationError( 'Has to be either ".pdb" or ".zip"')
    else:
        raise validators.ValidationError( 'Please provide file' )

    
class InputForm(FlaskForm):
    # creation of input fields
    pdb = FileField('Upload a pdb file:' , validators = [check_ending] )
    email = StringField('Email*:', validators=[Email()])
    tag = StringField('Tag:', validators=[DataRequired()])
    hetatm = BooleanField( 'Hetatms?')
    highres = BooleanField( 'High resolution?')
    submit = SubmitField('Analyse')

    def validate(self):
        print(self.pdb)
        fn = secure_filename(self.pdb.data.filename)
        print("validate:",fn)
        return '.' in fn and (fn.rsplit('.', 1)[-1] == 'pdb')


def send_email(user, link):
    log = open( 'calc.log', 'w' )
    log.write( 'send mail\n')
    log.write( os.getcwd() + '\n')
    with open( 'mail.txt', 'w') as out:
        out.write('From: voronoia@proteinformatics.de\n')
        out.write('Subject: Voronoia results \n')
        out.write('To: ' + user + '\n\n')
        out.write('hello  ' + user + '!\n\n')
        out.write('your voronoia calculation is done. \n')
        out.write('you can view the results here: \n\n' + link + '\n\n')
        out.write('thanks for using voronoia.\n\n')
        out.write('have a nice day!\n\n')
    os.system( 'sendmail -t < mail.txt' )
    log.close()

@app.route('/')
def index():
    return render_template('home.html')


def execute_cmd(cmd):
    p = subprocess.check_output(cmd)


def calculation(filename, output_dir, email, job, res, keepwater):
    #execute_cmd(["voronoia.py",filename , "-o", output_dir,"-vd"])
    #execute_cmd([app.config['APP_PATH'] + "get_holes.py", output_dir,"protein.vol.extended.vol"])
    #print([app.config['SCRIPTS_PATH'] + "run.sh", filename, output_dir])

    execute_cmd(['cp',app.config['APP_PATH'] + 'file_format.txt', output_dir + '/.'])
    
    keepcmd = ""
    if keepwater == 'keepall':
        keepcmd = "--keep_water" # FLAG
    elif keepwater == 'eraseall':
        # remove waters
        keepcmd = "ERASEWATER"
    
    if filename[-4:] == ".pdb":
        if res != '':
            resolution = "0.1"
        else:
            resolution = '0.4'
        execute_cmd([app.config['SCRIPTS_PATH'] + "run.sh", filename, output_dir, "--ex", resolution, keepcmd ])
    elif filename[-4:] == ".zip":
        resolution = '0.4'
        execute_cmd( ['unzip', filename, '-d', output_dir])
        filelist = os.listdir( output_dir )
        count = 0
        for f in filelist:
            if f[-4:] != '.pdb': continue
            count += 1
            if count > 100: break
            execute_cmd([app.config['SCRIPTS_PATH'] + "run.sh", f, output_dir, "--ex", resolution, keepcmd])

    # create zip file
    os.chdir(output_dir)
    cmd = ['zip','voronoia_' + job.replace(' ','') + '.zip','file_format.txt']
    checker=False
    for f in os.listdir( '.'):
        if ".vor.pdb" in f or '_holes.pdb' in f or '_neighbors.pdb' in f:
            cmd.append( f)
            checker=True
    if checker:
        execute_cmd( cmd )
    
    # optionally send email
    if email != 'anonymous':
        #with app.app_context():
        with app.app_context(), app.test_request_context():
            results_link = url_for('results', user=email, job=job)
            send_email(email, 'http://www.proteinformatics.de/voronoia' + results_link)


            
def start_thread(function, args, name):
    t = threading.Thread(target=function, name=name, args=args)
    t.deamon = True
    t.start()


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = InputForm()
    if request.method == 'GET':
        return render_template('submit.html', form=form, example_pdb=example_pdb)

    # get pdb file
    f = request.files['pdb']
    if f.filename == '':
        # if no file was uploaded, the user has loaded the example
        print('load example')
        f = FileStorage(open(app.config['EXAMPLES_DIR'] + example_pdb, 'rb'))

    # atomRadii = request.form.get('options')
    tag = request.form['tag']
    email = request.form['email']

    try:
        keepwater = request.form['selector']
        #print( 'keep:', keepwater)
    except:
        keepwater=""
                

    try:
        highres = request.form['highres']
    except:
        highres = ""

        
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
        return render_template('submit.html', form=form, error_str='tag "' + tag + '" already exists for user "' + email + '"', example_pdb=example_pdb)
        
    # save file
    filename = output_dir + os.path.basename( f.filename) #output_dir + "protein.pdb"
    #print( "FILE: ", filename)
    f.save(filename) 

    start_thread(calculation, [filename, output_dir, email, tag, highres, keepwater], 'zip')

#    print('submitted')
    return redirect(url_for('progress', user=email, job=tag)) 


@app.route('/status/<user>/<job>')
def status(user, job):
    # returns info about the status of the calculation
    status = 'running'
    fname = os.path.join(app.config['USER_DATA_DIR'], user, job, "voronoia_" + job + ".zip") #"protein_holes.pdb")
    #print("exists?: ",fname,job)
    if os.path.isfile(fname):
        status = 'finished'
        #print('yes')
    if status == 'running':
        fname = os.path.join(app.config['USER_DATA_DIR'], user, job, "failure.txt")
        #print("exists?: ",fname,job)
        if os.path.isfile(fname):
            status = 'Error'   

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
@app.route('/results/<user>/<job>/<prot>')
def results(user, job, prot=""):
    f = os.path.join(app.config['USER_DATA_DIR'], user, job, "voronoia_" + job + ".zip")
    #print( "results:", f)
    if os.path.isfile(f):
        allmols = []
        after = ""
        for ff in os.listdir( os.path.join(app.config['USER_DATA_DIR'], user, job ) ):
            if ".vor.pdb" in ff:
                allmols.append( ff[:-8])
        if len(allmols) == 1:
            prot = allmols[0]
        elif len(allmols) > 1:
            if prot == "":
                prot = allmols[0]
                after = allmols[1]
            else:
                try:
                    indx = allmols.index( prot )
                    after = allmols[ (indx+1) % len(allmols) ]
                except(ValueError):
                    print( 'ERROR:', prot, 'not found in', allmols)
        return render_template('results.html', user=user, job=job , mol=prot, nextmol=after ) #, lic_selection=get_lic_selection(user, job))
    return redirect(url_for('progress', user=user, job=job))


@app.route('/db-results/<pdb>')
def db_results(pdb):
    #return render_template('db_results.html', pdb=pdb, lic_selection=get_db_lic_selection(pdb))
    return render_template('db_results.html', pdb=pdb)


@app.route('/fs-results/<user>/<job>')
@app.route('/fs-results/<user>/<job>/<prot>')
def fs_results(user, job, prot=""):
    return render_template('fullscreen_results.html', user=user, job=job, mol=prot)

@app.route('/fullmenu/<user>/<job>/<mol>')
def fullmenu(user, job, mol):
    return render_template('fullmenu.html', user=user, job=job, mol=mol)

@app.route('/db-fullmenu/<mol>')
def db_fullmenu(  mol):
    return render_template('db_fullmenu.html', mol=mol)


@app.route('/db-fs-results/<pdb>')
def db_fs_results(pdb):
    return render_template('db_fullscreen_results.html', pdb=pdb)


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


@app.route('/db-downloads/<filename>')
def db_download(filename):
    path = app.config['DATABASE_DIR']
    if  '.zip' in filename and not os.path.exists(path + filename ):
        os.chdir(path)
        basename = filename[:-4]
        with ZipFile( str(filename) , 'w' ) as w:
            for f in [ str(basename + "_holes.pdb"), str(basename + '_neighbors.pdb'), str(basename + '.vor.pdb') ]:
                w.write( f )
            w.write('file_format.txt')
                
    return send_from_directory(path, filename)


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
    pdbid = request.form['pdb-id'].lower()
    pdb =  app.config['DATABASE_DIR'] + pdbid + ".vor.pdb"
    print( pdb)
    if not os.path.exists(pdb):
        print( pdb + 'not found')
        message = "<" + pdbid + "> does not exist in database, please download directly from PDB and use 'submit'"
        return render_template( 'database.html', message=message)
    return redirect(url_for('db_results', pdb=pdbid))


@app.route('/methods')
def methods():
    return render_template('methods.html')


@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

@app.route('/down')
def down():
    return render_template('download.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')



if __name__ == '__main__':
    app.run(ssl_context= ('/etc/apache2/ssl/cert-11043954791332636805298309362.pem', '/etc/apache2/ssl/key.pem' ))
