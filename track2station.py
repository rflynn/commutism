#!/usr/bin/env python2.7
# vim: set ts=4 et:

import sqlite3

import loc

def latlong2station((lat, long_)):
    for borough, items in subwaystations['NYC'].items():
        for key, val in items.items():
            if latlongmatch((lat, long_), (val['loc']['lat'], val['loc']['long'])):
                return key
    return None

if __name__ == '__main__':



    print latlong2station((0., 0.))
    print latlong2station((-73.976522, 40.7528))
    print latlong2station((-73.97652, 40.752))
    print latlong2station((-73.9765, 40.752))
    print latlong2station((-73.976, 40.752))
    print latlong2station((-73.97, 40.75))

