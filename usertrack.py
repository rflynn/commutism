#!/usr/bin/env python2.7
# vim: set ts=4 et:

from pprint import pprint
import sqlite3
import time

import loc

# database connection
dbx = sqlite3.connect('./commutual.sqlite3', check_same_thread=False)
dbx.isolation_level = 'DEFERRED'
dbx.row_factory = sqlite3.Row

def uid_point_add(uid, ts, pt):
    uid = long(uid)
    lat = pt['lat']
    long_ = pt['long']
    acc = pt['acc']
    speed = pt.get('speed')
    now = long(time.time())
    c = dbx.cursor()
    c.execute('''
insert into usertrack (serverts, ts, uid, lat, long_, acc, speed)
values                (?,        ?,  ?,   ?,   ?,     ?,   ?);
''',
              (now, ts, uid, lat, long_, acc, speed))
    dbx.commit()
    c.close()

def uid_points_get(uid, ts_from, ts_to=None):
    uid = long(uid)
    ts_to = ts_to or long(time.time())
    c = dbx.cursor()
    c.execute('''
select strftime('%Y-%m-%d %H:%M:%S', ts - (60 * 60 * 5), 'unixepoch') as ts, lat, long_ as long, acc, round(speed, 6) as speed
from usertrack
where uid=?
and acc <= 100
and ts between ? and ?
''', (uid, ts_from, ts_to))
    rows = c.fetchall()
    c.close()
    return list(map(dict, rows))

def uid_points_classify(uid, ts_from):
    return [(r, st)
                for r,st in [(r, loc.latlong2station((r['lat'], r['long'])))
                    for r in uid_points_get(uid, ts_from)]]

if __name__ == '__main__':
    pprint(uid_points_classify('3060004380151080232', 0), width=180)

