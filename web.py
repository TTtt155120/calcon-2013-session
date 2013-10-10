"""
Module for the CALCON 2013 RDF & BIBFRAME Session Presentation

Copyright (C) 2013 Jeremy Nelson 

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
__version_info__ = ('0', '0', '5')
__version__ = '.'.join(__version_info__)
__author__ = "Jeremy Nelson"
__license__ = 'GPL v2'
__copyright__ = '(c) 2013 by Jeremy Nelson'

import argparse
import hashlib
import json
import os
import sqlite3

from flask import Flask, g, redirect, render_template, url_for
from flask import flash, jsonify, request, session
from flask.ext.login import LoginManager, login_user, login_required, logout_user
from flask.ext.login import make_secure_token, UserMixin, current_user
##from flaskext.bcrypt import Bcrypt

from flask_oauth import OAuth
from contextlib import closing

from flup.server.fcgi import WSGIServer

GOOGLE_SETTINGS = json.load(open('google_auth.json', 'rb'))
##GOOGLE_SETTINGS = None

DATABASE = 'calcon2013_badges.sqlite'

def connect_db():
    return sqlite3.connect(DATABASE)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_db()
    return db
    
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        cursor = db.cursor()
        for name in SLIDES:
            slides = SLIDES.get(name)
            for slide in slides:
                cursor.execute("INSERT INTO slides (label, name) VALUES (?,?)",
                               (slide.get('label'),
                                slide.get('name'),))
                db.commit()

oauth = OAuth()

##google = oauth.remote_app(
##    'google',
##    base_url='https://www.google.com/accounts',
##    authorize_url=GOOGLE_SETTINGS['web'].get('auth_uri'),
##    request_token_url=None,
##    request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
##                          'response_type': 'code'},
##    access_token_url=GOOGLE_SETTINGS['web'].get('token_uri'),
##    access_token_method='POST',
##    access_token_params={'grant-type': 'authorization_code'},
##    consumer_key=GOOGLE_SETTINGS['web'].get('client_id'),
##    consumer_secret=GOOGLE_SETTINGS['web'].get('client_secret'))
    
    
                          

app = Flask(__name__,
            static_url_path='/calcon-2013-session/static')
login_manager = LoginManager()
login_manager.init_app(app)
## bcrypt = Bcrypt(app)

ANSWERS = json.load(open('answers.json', 'rb'))
app.secret_key = ANSWERS.pop('secret_key')

RESOURCES = {'article-books': [], 'websites': [] }
for name in ['anglo-american-cataloging-rules-second-edition.json',
             'bibframe-annotation-model.json',
             'bibframe-resource-types-discussion-paper.json',
             'bibframe-use-cases-and-requirements.json',
             'bibliographic-framework-as-a-web-of-data.json',
             'building-a-library-app-portfolio-with-redis-and-django.json',
             'on-bibframe-authority.json',
             'understanding-marc-bibliographic.json']:
    RESOURCES['article-books'].append(
        json.load(
            open(os.path.join('static',
                              'js',
                              name),
                 'rb')))
for name in ['rda-resource-description-and-access-vocabularies.json',
             'rda-toolkit.json',
             'redis.json']:
   RESOURCES['websites'].append(
        json.load(
            open(os.path.join('static',
                              'js',
                              name),
                 'rb')))

SLIDES = json.load(open('slides.json'))

URL_PREFIX = '/calcon-2013-session'



class User(UserMixin):

    def __init__(self, email, id, active=True):
        self.id = id
        self.email = email
        self.active = active
        self.badge = {'history': [], 'quiz_results': []}

    def get_badge(self):
        self.badge['score'] = 0
        badge_query = get_db().cursor().execute(
            """SELECT slides.name, slides.label, slide_results.created_on,
                 slide_results.q1, slide_results.q2, slide_results.q3
                 FROM slides, slide_results
                 WHERE slide_results.participant_id=? AND slides.id=slide_results.slide_id""",
            (self.id,))
        badge_results = badge_query.fetchall()
        for row in badge_results:
            self.badge['quiz_results'].append(
                {'label': row[1],
                 'taken': row[2],
                 'q1': row[3],
                 'q2': row[4],
                 'q3': row[5],
                 'total': sum([row[3],
                               row[4],
                               row[5]])})
            self.badge['score'] += self.badge['quiz_results'][-1].get('total')
        return self.badge
        

    def get_id(self):
        return self.id

    def is_active(self):
        return self.active

    def get_auth_token(self):
        return make_secure_token(self.email,
                                 key='deterministic')
        


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    
@login_manager.user_loader
def load_user(userid):
    user_query = get_db().cursor().execute(
        """SELECT * FROM participant WHERE identity_hash=?""",
        (userid,))
    user_result = user_query.fetchone()
    if user_result is None:
        return None
    return User(id=userid,
                email=user_result[3])
                
@app.route('{0}/bibframe-rda-badge.json'.format(URL_PREFIX))
def badge_class_json():
    """
    Following examples at <https://github.com/mozilla/openbadges/wiki/Assertions>
    """
    return jsonify(
            {"name": "CALCON 2013 - BIBFRAME and RDA Badge",
             "description":
             "Introduction to BIBFRAME and RDA presented by Jeremy Nelson at CALCON 2013 RDA Session",
             "image": "http://tuttdemo.coloradocollege.edu{0}".format(
                 url_for('static', filename="img/bibframe-rda-badge.png")),
             "criteria": "http://tuttdemo.coloradocollege.edu{0}".format(
                 url_for('badge')),
             "tags": ["BIBFRAME", "CALCON 2013", "RDA"],
             "issuer": "http://tuttdemo.coloradocollege.edu{0}".format(
                 url_for('badge_issuer_org'))})
             
@app.route('{0}/badge-issuer-organization.json'.format(URL_PREFIX))
def badge_issuer_org():
    return jsonify(
        {"name": "Colorado College Tutt Library Systems and Metadata Services",
         "image": "http://tuttdemo.coloradocollege.edu{0}".format(
             url_for('static', 'img/tutt-library-spring.png')),
         "url": "http://www.coloradocollege.edu/library/",
         "email": "jeremy.nelson@coloradocollege.edu",
         "revocationList": "http://tuttdemo.coloradocollege.edu{0}".format(
             url_for('badge_revoked'))})

@app.route('{0}/revoked.json'.format(URL_PREFIX))
def badge_revoked():
    return jsonify({})

           

           
@app.route('{0}/badge.html'.format(URL_PREFIX))
def badge():
    participant, slide_results = None, []
    if current_user.is_authenticated():
        participant_query = get_db().cursor().execute(
            "SELECT email FROM participant WHERE identity_hash=?",
            (current_user.id,))
        results = participant_query.fetchone()
        participant={'email': results[0]}
        quiz_query = get_db().cursor().execute(
            "SELECT * FROM slide_results WHERE participant_id=?",
            (current_user.id,))
        participant['quiz_results'] = quiz_query.fetchall()
    return render_template('badge.html',
                           category='addendum',
                           slides=SLIDES,
                           participant=participant,
                           user=current_user)


@app.route('{0}/glossary.html'.format(URL_PREFIX))
def glossary():
    return render_template("glossary.html",
                           category='addendum',
                           slides=SLIDES,
                           user=current_user)

@app.route('{0}/grade'.format(URL_PREFIX),
           methods = ['POST', 'GET'])
def grade():
    score = 0
    cursor = get_db().cursor()
    # Need to keep 
    if request.method == 'POST':
        slide = request.form['slide']
        if slide in session:
            return jsonify(
                {'error': 'Quiz for {0} with a score of {1} already exists'.format(
                    slide,
                    session[slide])})            
        if slide in ANSWERS:
            q1, q2, q3 = 0, 0, 0
            q1_answer = request.form.getlist('q1')
            if q1_answer == ANSWERS[slide].get('q1'):
                q1 = 1
            q2_answer = request.form.getlist('q2')
            if q2_answer == ANSWERS[slide].get('q2'):
                q2 = 1
            q3_answer = request.form.getlist('q3')
            if q3_answer == ANSWERS[slide].get('q3'):
                q3 = 1
            if current_user:
                slide_result = cursor.execute(
                    "SELECT id FROM slides WHERE name=?",
                    (slide,)).fetchall()
                if len(slide_result) == 1:
                    slide_id = slide_result[0][0]
##                print(slide_id, current_user.id)
                # Insert quiz results to db
                cursor.execute("""INSERT INTO slide_results
 (slide_id, participant_id, q1, q2, q3) VALUES (?, ?, ?, ?, ?)""",
                           (slide_id,
                           current_user.id,
                           q1,
                           q2,
                           q3))
                get_db().commit()
            score = sum([q1, q2, q3])
            session[slide] = score
        return jsonify({'score': score })


@app.route('{0}/login'.format(URL_PREFIX),
       methods=['GET', 'POST'])
def login():
##    return google.authorize(callback='http://tuttdemo.coloradocollege.edu/')
    if request.method == 'POST':
        cur = get_db().cursor()
        email = request.form.get('email')
        raw_pwd = request.form.get('pw')
        email_query = cur.execute("SELECT identity_hash, pwd_hash FROM participant WHERE email=?",
                                  (email,))
        email_results = email_query.fetchall()
        if len(email_results) == 1:
            saved_id_hash, saved_pwd_hash = email_results[0]
            existing_hash = hashlib.sha256(raw_pwd)
            existing_hash.update(app.secret_key)
            if saved_pwd_hash == existing_hash.hexdigest():
                user = User(id=saved_id_hash,
                            email=email)
                login_user(user)
            else:
                raise ValueError("Incorrect login")
        return redirect(request.args.get("next") or url_for("home"))
    return render_template("login.html",
                           category='home',
                           slides=SLIDES,
                           user=current_user)

@app.route('{0}/logout'.format(URL_PREFIX),
           methods=['GET', 'POST'])
def logout():
    logout_user()
    flash("Logged out")
    return redirect(url_for("home"))
    

@app.route('{0}/register'.format(URL_PREFIX),
           methods=['POST'])
def register():
    raw_email = request.form.get('email_address')
    email_checkquery = get_db().cursor().execute(
        """SELECT identity_hash FROM participant WHERE email=?""",
        (raw_email,))
    if len(email_checkquery.fetchall()) > 0:
        flash("{0} already registered for this badge".format(
            raw_email))
        return redirect(url_for("badge"))
    pwd_one = request.form.get('password')
    pwd_confirm = request.form.get('copy-password')
    if pwd_one != pwd_confirm:
        flash("Error passwords do not match")
    else:
        identity_hash = hashlib.sha256(raw_email)
        identity_hash.update(app.secret_key)
        pwd_hash = hashlib.sha256(pwd_one)
        pwd_hash.update(app.secret_key)
        db = get_db()
        db.cursor().execute(
            """INSERT INTO participant (identity_hash, email, pwd_hash)
            VALUES (?, ?, ?)""",
            (identity_hash.hexdigest(),
             raw_email,
             pwd_hash.hexdigest()))
        db.commit()
        user = User(id=identity_hash.hexdigest(),
                    email=raw_email)
        login_user(user)
        flash("Successfully registered for CALCON2013 BIBFRAME and RDA Badge")
    return redirect(url_for("badge"))
                           
@app.route('{0}/resources.html'.format(URL_PREFIX))
def resources():
    return render_template("resources.html",
                           category='addendum',
                           resources=RESOURCES,
                           slides=SLIDES,
                           user=current_user)

@app.route('{0}/resources/<path:filename>.json'.format(URL_PREFIX))
def resource(filename):
    for resource in RESOURCES.get('article-books') + RESOURCES.get('websites'):
        if filename == resource.get('name'):
            return jsonify(resource)
    return None
    

@app.route('{0}/<track>/<path:slide>'.format(URL_PREFIX))
def slide(track, slide):
    current, last_slide, next_slide, badge_dict = None, None, None, {}
    for i, row in enumerate(SLIDES[track]):        
        if row.get('name') == slide:
            current = row
            if i-1 > -1:
                last_slide = SLIDES[track][i-1]
                last_slide['url'] = '{0}/{1}/{2}'.format(
                    URL_PREFIX,
                    track,
                    last_slide.get('name'))
            if i+1 < len(SLIDES[track]):
                next_slide = SLIDES[track][i+1]
                next_slide['url'] = '{0}/{1}/{2}'.format(
                    URL_PREFIX,
                    track,
                    next_slide.get('name'))
    if current_user.is_authenticated():
        badge_dict = current_user.get_badge()
    return render_template("{0}.html".format(slide),
                           badge=badge_dict,
                           category='slide',
                           current=current,
                           last_slide=last_slide,
                           next_slide=next_slide,
                           slides=SLIDES,
                           track=track,
                           user=current_user)

@app.route('{0}/'.format(URL_PREFIX))
def home():
    default_css = url_for('static', filename='default.css')
    return render_template('index.html',
                           category='home',
                           slides=SLIDES,
                           user=current_user)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run CALCON 2013 Session Presentation')
    parser.add_argument('mode',
                    help='Run in either prod (production) or dev (development)')
    mode = parser.parse_args().mode
    host = '0.0.0.0'
    port = 8130
    if mode == 'prod':
        WSGIServer(app,
                   bindAddress='{0}:{1}'.format(host,
                                                port)).run()
    elif mode == 'dev':
        app.run(host=host,
                port=port,
                debug=True)
    else:
        print("Unknown mode {0}, should be prod or dev".format(mode))
