#!/usr/bin/env python2.7
# vim: set ts=4 et:

from flask import Flask, render_template, request, redirect, url_for, make_response

from datetime import date, datetime, timedelta
import random
import sqlite3
import time
import urllib
from urlparse import urlparse

# flask app core
app = Flask(__name__, static_url_path='')

# strip whitespace after template rendering
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# database connection
dbx = sqlite3.connect('./commutual.sqlite3', check_same_thread=False)
dbx.isolation_level = 'DEFERRED'
dbx.row_factory = sqlite3.Row

def newuid():
    return str((long(time.time()) << 31) | random.getrandbits(31))

def req2uid(request):
    return request.cookies.get('uid') or newuid()

def dotrack(response, uid):
    response.set_cookie('uid', uid)
    return response

@app.route('/', methods=['GET'])
def root():
    #return 'Hello, world!'
    #return 'Hello from Flask! (%s)' % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    uid = req2uid(request)
    resp = make_response(render_template('index.html'))
    return dotrack(resp, uid)

def usertrack(db, request, uid):
    ts = int(time.time())
    lat = float(request.args.get('lat'))
    long_ = float(request.args.get('long'))
    acc = int(float(request.args.get('acc')))
    uid = long(uid)
    c = db.cursor()
    c.execute('insert into usertrack (ts, uid, lat, long_, acc) values (?, ?, ?, ?, ?);',
              (ts, uid, lat, long_, acc))
    db.commit()
    c.close()

@app.route('/api/v0/track/me')
def track():
    uid = req2uid(request)
    usertrack(dbx, request, uid)
    resp = make_response('')
    return dotrack(resp, uid)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0',
            port=80)
