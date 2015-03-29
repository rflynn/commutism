#!/usr/bin/env python2.7
# vim: set ts=4 et:

from flask import Flask, jsonify, make_response, render_template, request
from flask.ext.cors import CORS

import datetime
import json
import random
import sqlite3
import time
import urllib
from urlparse import urlparse

# flask app core
app = Flask(__name__, static_url_path='')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=3650)

cors = CORS(app)

# strip whitespace after template rendering
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

# database connection
dbx = sqlite3.connect('./commutual.sqlite3', check_same_thread=False)
dbx.isolation_level = 'DEFERRED'
dbx.row_factory = sqlite3.Row

def maybefloat(s):
    try:
        return float(s)
    except:
        return None

def newuid():
    return str((long(time.time()) << 31) | random.getrandbits(31))

# TODO: save in Redis or sumthn
Uidh = dict()

def xuidh2uid(request):
    xuidh = request.headers.get('X-Uidh')
    if not xuidh:
        return None
    return Uidh.get(xuidh)

def req2uid(request):
    return request.cookies.get('uid') or xuidh2uid(request) or newuid()

def dotrack(response, uid):
    response.set_cookie('uid', uid)
    return response

@app.route('/', methods=['GET'])
def root():
    uid = req2uid(request)
    resp = make_response(render_template('index.html',
                         latest_users=latest_users(dbx)))
    return dotrack(resp, uid)

@app.route('/latency', methods=['GET'])
def latency_():
    uid = req2uid(request)
    resp = make_response(render_template('latency.html'))
    return dotrack(resp, uid)

@app.route('/map', methods=['GET'])
def map_():
    uid = req2uid(request)
    resp = make_response(render_template('map.html'))
    return dotrack(resp, uid)

def latest_users(db):
    c = db.cursor()
    c.execute('''
select distinct uid as uid, max(ts) as ts, count(*) as cnt
from usertrack
group by uid
having count(*) > 1
order by max(ts);
''')
    rows = c.fetchall()
    c.close()
    return rows

def usertrack(db, request, uid):
    # interesting: iPhones will save up XMLHttpRequests and fire them off in batches
    # this means the client ts can differ from the serverside and be legit... we're being sent
    # older data. if we record the timestamp serverside the datapoints don't line up..
    # however, we should limit how far back the ts's are allowed to be sent from...
    # TODO: send ts in UTC, record server ts separately and enforce clientside tses within a given limit...
    now = int(time.time())
    ts = int(request.args.get('ts') or now)
    lat = round(float(request.args.get('lat')), 6)
    long_ = round(float(request.args.get('long')), 6)
    acc = int(float(request.args.get('acc')))
    speed = maybefloat(request.args.get('speed'))
    uid = long(uid)
    c = db.cursor()
    c.execute('''
insert into usertrack (serverts, ts, uid, lat, long_, acc, speed)
values                (?,        ?,  ?,   ?,   ?,     ?,   ?);
''',
              (now, ts, uid, lat, long_, acc, speed))
    db.commit()
    c.close()

@app.route('/api/v0/track/me')
def track():
    uid = req2uid(request)
    print request.headers
    usertrack(dbx, request, uid)
    resp = make_response('')
    return dotrack(resp, uid)

@app.route('/robots.txt')
def robots():
    print request.headers
    resp = make_response('''User-agent: *
Crawl-delay: 10
Disallow: /api/
''')
    resp.headers['Content-Type'] = 'text/plain'
    return resp

def get_user_since(db, uid):
    uid = long(uid)
    c = db.cursor()
    c.execute('''
select ts, lat, long_, acc
from usertrack
where uid=?
-- and ts >= strftime('%s','now') - (5*24*60*60) -- XXX: commented out, handy later
''', (uid,))
    rows = c.fetchall()
    c.close()
    return [[r['ts'], round(r['lat'], 6), round(r['long_'], 6), r['acc']]
                for r in rows]

# TODO: add page that allows selection of recent paths:
# sqlite3 commutual.sqlite3 'select distinct uid, count(*) from usertrack group by uid having count(*) > 1 order by max(ts);'

@app.route('/api/v0/me/today', methods=['GET'])
def me_24hrs():
    uid = req2uid(request)
    return jsonify(**{'p':get_user_since(dbx, request.args.get('uid', '3065451368030356068'))})

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0',
            port=80)
