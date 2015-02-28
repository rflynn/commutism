#!/usr/bin/env python2.7
# vim: set ts=4 et:

import yaml
from math import sqrt

subwaystations = dict()
with open('./data/ref/nyc-subway-station-complexes-2013.yml') as f:
    subwaystations = yaml.load(f)

def locdiff((xlat, xlong), (ylat, ylong)):
    return round(sqrt((abs(xlat - ylat)**2) + (abs(xlong - ylong)**2)), 5)

def latlong2station((lat, long_)):
    for borough, items in subwaystations['NYC'].items():
        v, k = min((locdiff((lat, long_),
                            (val['loc']['lat'], val['loc']['long'])),
                    key) for key, val in items.items())
        if v <= 0.001:
            return k, v
    return None

if __name__ == '__main__':
    print latlong2station((0., 0.))
    print latlong2station((-73.976522, 40.7528))
    print latlong2station((-73.97652, 40.752))
    print latlong2station((-73.9765, 40.752))
    print latlong2station((-73.976, 40.752))
    print latlong2station((-73.97, 40.75))

