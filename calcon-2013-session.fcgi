#!/home/jpnelson/jpn-app-dev/bin/python
from flup.server.fcgi import WSGIServer
from web import app

if __name__ == '__main__':
    WSGIServer(app,
               bindAddress=('0.0.0.0',8130)).run() 
