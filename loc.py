#!/usr/bin/env python2.7
# vim: set ts=4 et:

from math import sqrt
from pprint import pprint
from itertools import takewhile, groupby, starmap

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
        if station['edges']:
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
    return [x for x,y in
                sorted([x for x in SubwayStations['Station'].items()
                    if x[1]['loc']['lat'] != 0.0 and x[1]['loc']['long'] != 0.0],
                  key=lambda x: latlongdist(latlong, x[1]['loc']),
                  reverse=False)[:20]]

def latlong2station((lat, long_)):
    return stations_nearest({'lat': lat,
                             'long': long_})

if __name__ == '__main__':
    import sys
    import itertools
    #print latlong2station((0., 0.))
    #print latlong2station((-73.976522, 40.7528))
    #print latlong2station((-73.97652, 40.752))
    #print latlong2station((-73.9765, 40.752))
    #print latlong2station((-73.976, 40.752))
    #print latlong2station((40.75, -73.97))
    print latlong2station((40.704294, -73.919277)) # DeKalb (L)
    print latlong2station((40.699377, -73.922061)) # 171 Stanhope
    print latlong2station((40.704283, -74.011963)) # 80 Broad St
    _171_Stanhope = {'lat': 40.699377, 'long': -73.922061}
    _80_Broad_St = {'lat': 40.704283, 'long': -74.011963}
    Stations_Nearest_171_Stanhope = stations_nearest(_171_Stanhope)[:5]
    Stations_Nearest_80_Broad_St = stations_nearest(_80_Broad_St)[:5]

    print '--------------'

    pprint(Stations_Nearest_171_Stanhope, width=150)
    pprint(Stations_Nearest_80_Broad_St, width=150)

    def shortest_path(g, source=None, target=None):
        try:
            return nx.shortest_path(g, source=source, target=target)
        except nx.exception.NetworkXNoPath:
            return None

    print '--------------'
    #Trips = [((x,y), set(map(tuple,nx.all_simple_paths(SubwayGraphX, source=x, target=y))))
    Trips = [shortest_path(SubwayGraphX, source=x, target=y)
                for x, y in itertools.product(Stations_Nearest_171_Stanhope,
                                              Stations_Nearest_80_Broad_St)]

    def distance_walking(path):
        st1 = SubwayStations['Station'][path[0]]
        st2 = SubwayStations['Station'][path[-1]]
        return ((latlongdist(_171_Stanhope, st1['loc']) +
                 latlongdist(_80_Broad_St, st2['loc'])), len(path))

    def station_distance(st1, st2):
        dist = latlongdist(SubwayStations['Station'][st1]['loc'],
                           SubwayStations['Station'][st2]['loc'])
        print 'station_distance', st1, st2, dist
        return dist

    def distance_traveled(path):
        # given a path, calculate the actual distance traveled
        st1 = SubwayStations['Station'][path[0]]
        st2 = SubwayStations['Station'][path[-1]]
        walk_to_first = latlongdist(_171_Stanhope, st1['loc'])
        walk_from_last = latlongdist(_80_Broad_St, st2['loc'])
        print list(starmap(station_distance, zip(path, path[1:])))
        between_stations = sum(starmap(station_distance, zip(path, path[1:])))
        return walk_to_first + between_stations + walk_from_last

    Trips2 = sorted(set(tuple(trip) for trip in Trips if trip),
                     key=lambda path: distance_traveled(path),
                     reverse=False)
    Trips3 = [(round(distance_traveled(x), 5), list(x)) for x in Trips2]

    pprint(Trips3, width=500)

    # join common prefixes

    def longest_prefix(x, y):
        if not x or not y:
            return 0
        return len(list(takewhile(lambda x: x is True,
                    [x == y for x, y in zip(x, y)])))

    lps = [(longest_prefix(x, y), (x, y))
            for x, y in zip(Trips3, Trips3[1:])]
    lps2 = [list(y) for x, y in groupby(lps, lambda x: x[0] > 0) if x]

    def uniques(l):
        x = (l[0][0], [x[1][0] for x in l])
        if len(l) > 1:
            x[1].append(l[-1][1][1])
        return x

    lps3 = [uniques(x) for x in lps2]

    def apply_prefix(foo):
        n, lists = foo
        prefix = lists[0][:n]
        suffixes = [l[n:] for l in lists]
        return (prefix, suffixes)

    lps4 = [apply_prefix(x) for x in lps3]

    def print_prefix((prefix, lists)):
        s = str(prefix)
        print s, lists[0]
        for l in lists[1:]:
            print ' ' * len(s), l

    map(print_prefix, lps4)

    print '--------------'

    sys.exit(0)

    print 'SubwayGraphX:'
    print SubwayGraphX.edges(keys=True)
    print 'paths:'
    #print nx.shortest_path(SubwayGraphX, source='14 St-Union Sq', target='DeKalb Av (L)')
    #print nx.shortest_path(SubwayGraphX, source='14 St-Union Sq', target='Bowling Green')
    print nx.shortest_path(SubwayGraphX, source='Bowling Green', target='DeKalb Av (L)')

    print nx.shortest_path(SubwayGraphX, source='Broad St', target='Central Av')

    print nx.shortest_path(SubwayGraphX, source='High St', target='Central Av')
    print nx.shortest_path(SubwayGraphX, source='High St', target='Bowling Green')

    print 'Times Sq to Bowling Green...'
    print nx.shortest_path(SubwayGraphX, source='Times Sq-42 St', target='Bowling Green')

    all_paths = nx.all_simple_paths(SubwayGraphX,
                                    source='Times Sq-42 St',
                                    target='Bowling Green')
    all_paths = sorted(set(map(tuple,all_paths)), key=lambda l: len(l))
    pprint(all_paths, width=150)

    print 'Bowling Green -> DeKalb Av...'
    all_paths = nx.all_simple_paths(SubwayGraphX,
                                    source='Bowling Green',
                                    target='DeKalb Av (L)')
    all_paths = sorted(set(map(tuple,all_paths)), key=lambda l: len(l))
    pprint(all_paths, width=150)

    #pprint(nx.all_pairs_dijkstra_path(SubwayGraphX, 'Bowling Green', 'DeKalb Av (L)'), width=150)

    '''
    ['__path__', 'all_pairs_dijkstra_path', 'all_pairs_dijkstra_path_length', 'all_pairs_shortest_path', 'all_pairs_shortest_path_length', 'all_shortest_paths', 'all_simple_paths', 'astar_path', 'astar_path_length', 'average_shortest_path_length', 'bidirectional_shortest_path', 'dijkstra_path', 'dijkstra_path_length', 'has_path', 'path_graph', 'shortest_path', 'shortest_path_length', 'shortest_paths', 'simple_paths', 'single_source_dijkstra_path', 'single_source_dijkstra_path_length', 'single_source_shortest_path', 'single_source_shortest_path_length']
    '''

    '''
    print ''
    pprint(nx.all_pairs_shortest_path(SubwayGraphX), width=150)
    '''
