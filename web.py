__author__ = "Jeremy Nelson"

import json

from flask import Flask, render_template, url_for
from flask import jsonify, request, session

app = Flask(__name__)

ANSWERS = json.load(open('answers.json', 'rb'))
app.secret_key = ANSWERS.pop('secret_key')

SLIDES = {'bibframe':[{'name': 'history',
                       'label': 'History of BIBFRAME'},
                      {'name': 'vocab-overview',
                       'label': 'BIBFRAME Vocabulary Overview'},
                      {'name': 'creative-works',
                       'label': 'Creative Works'},
                      {'name': 'annotations',
                       'label': 'Annotations'},
                      {'name': 'authorities',
                       'label': 'Authorities'},
                      {'name': 'instances',
                       'label': 'Instances'}],
          'rda': [{'name': 'aacrl2-is-to-rda',
                   'label': 'AACRL2 is to RDA...'},
                  {'name': 'marc21-is-to-BIBFRAME',
                   'label': '...as MARC21 is to BIBFRAME'},
                  {'name': 'rda-in-bibframe',
                   'label': 'RDA in BIBFRAME'},
                  {'name': 'bibframe-rlsp',
                   'label': 'BIBFRAME and the Redis Library Services Platform'}]}

URL_PREFIX = '/calcon-2013-session'

@app.route('{0}/badge.html'.format(URL_PREFIX))
def badge():
    return render_template('badge.html',
                           category='addendum',
                           slides=SLIDES)


@app.route('{0}/glossary.html'.format(URL_PREFIX))
def glossary():
    return render_template("glossary.html",
                           category='addendum',
                           slides=SLIDES)

@app.route('{0}/grade'.format(URL_PREFIX),
           methods = ['POST', 'GET'])
def grade():
    score = 0
    if request.method == 'POST':
        slide = request.form['slide']
        if slide in ANSWERS:
            q1_answer = request.form.getlist('q1')
            if q1_answer == ANSWERS[slide].get('q1'):
                score += 1
            q2_answer = request.form.getlist('q2')
            if q2_answer == ANSWERS[slide].get('q2'):
                score += 1
            q3_answer = request.form.getlist('q3')
            if q3_answer == ANSWERS[slide].get('q3'):
                score += 1
        if slide not in session:
            session[slide] = score
            return jsonify({'score': score })
        else:
            return jsonify(
                {'error': 'Quiz for {0} with a score of {1} already exists'.format(
                    slide,
                    session[slide])})

                           
@app.route('{0}/resources.html'.format(URL_PREFIX))
def resources():
    return render_template("resources.html",
                           category='addendum',
                           slides=SLIDES)
    
@app.route('{0}/open-badge/'.format(URL_PREFIX))
@app.route('{0}/open-badge/<action>'.format(URL_PREFIX))
def open_badge(action=None):
    if action is None:
        return "In Open Badge Base"
    else:
        return "In Open Badge {0}".format(action)

@app.route('{0}/<track>/<path:slide>'.format(URL_PREFIX))
def slide(track, slide):
    current, last_slide, next_slide = None, None, None
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
    return render_template("{0}.html".format(slide),
                           category='slide',
                           current=current,
                           last_slide=last_slide,
                           next_slide=next_slide,
                           slides=SLIDES,
                           track=track)

@app.route('{0}/'.format(URL_PREFIX))
def home():
    default_css = url_for('static', filename='default.css')
    return render_template('index.html',
                           category='home',
                           slides=SLIDES)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
