__author__ = "Jeremy Nelson"

from flask import Flask, render_template
app = Flask(__name__)

SLIDES = {'bibframe':[{'name': 'history',
                       'label': 'History of BIBFRAME'}],
          'rda': [{'name': 'aacrl2-and-rda',
                   'label': 'AACRL2 and RDA'},
                  {'name': 'marc21-and-BIBFRAME',
                   'label': 'MARC21 and BIBFRAME'},
                  {'name': 'rda-in-bibframe',
                   'label': 'RDA in BIBFRAME'}]}

URL_PREFIX = '/calcon-2013-session'

@app.route('{0}/'.format(URL_PREFIX))
def home():
    return render_template('index.html',
                           category='home',
                           slides=SLIDES)

if __name__ == '__main__':
    app.run(debug=True)
