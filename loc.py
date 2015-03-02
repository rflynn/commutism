#!/usr/bin/env python2.7
# vim: set ts=4 et:

from math import sqrt
from pprint import pprint

import networkx as nx
import yaml

SubwayStations = dict()
with open('./data/ref/nyc-subway-station-complexes-2013.yml') as f:
    SubwayStations = yaml.load(f)

#pprint(SubwayStations, width=150)

SubwayGraphX = nx.MultiDiGraph()

# build digraphs for each line
for name, station in SubwayStations['Station'].iteritems():
    if 'edges' in station:
        print name
        for to, lines in station['edges'].iteritems():
            if type(lines) != type([]):
                lines = [lines]
            for line in lines:
                SubwayGraphX.add_edge(name, to, key=line)
    else:
        print 'need edges: %s' % name

def latlongdist(x, y):
    return sqrt((abs(x['lat'] - y['lat'])**2) +
                (abs(x['long'] - y['long'])**2))

def stations_nearest(latlong):
    return sorted([x for x in SubwayStations['Station'].items()
                    if x[1]['loc']['lat'] != 0.0 and x[1]['loc']['long'] != 0.0],
                  key=lambda x: latlongdist(latlong, x[1]['loc']),
                  reverse=False)[:10]

def latlong2station((lat, long_)):
    latlong = {
        'lat': lat,
        'long': long_
    }
    nearest = stations_nearest(latlong)
    #print [(latlongdist(latlong, x[1]['loc']), x) for x in nearest]
    #print nearest, latlongdist(latlong, nearest[0][1]['loc']) if nearest else None
    name, station = nearest[0]
    #if latlongdist(latlong, station['loc']) <= 0.001:
    return {'name': name, 'station': station}
    #return None

if __name__ == '__main__':
    #print latlong2station((0., 0.))
    #print latlong2station((-73.976522, 40.7528))
    #print latlong2station((-73.97652, 40.752))
    #print latlong2station((-73.9765, 40.752))
    #print latlong2station((-73.976, 40.752))
    #print latlong2station((40.75, -73.97))
    print latlong2station((40.704294, -73.919277)) # DeKalb (L)
    print latlong2station((40.699377, -73.922061)) # 171 Stanhope
    print latlong2station((40.704283, -74.011963)) # 80 Broad St
    _80_Broad_St = {'lat': 40.704283, 'long': -74.011963}
    _171_Stanhope = {'lat': 40.699377, 'long': -73.922061}
    pprint(stations_nearest(_171_Stanhope)[:5], width=150)
    pprint(stations_nearest(_80_Broad_St)[:5], width=150)

    print 'SubwayGraphX:'
    print SubwayGraphX.edges(keys=True)
    print 'paths:'
    #print nx.shortest_path(SubwayGraphX, source='14 St-Union Sq', target='DeKalb Av (L)')
    #print nx.shortest_path(SubwayGraphX, source='14 St-Union Sq', target='Bowling Green')
    print nx.shortest_path(SubwayGraphX, source='Bowling Green', target='DeKalb Av (L)')
