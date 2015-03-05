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
                if isinstance(lines, dict):
                    # i've started marking up bus and train lines, but haven't got a consistent format down yet...
                    continue
                else:
                    if not isinstance(lines, list):
                        lines = [lines]
                    for line in lines:
                        SubwayGraphX.add_edge(name, to, key=line)
    else:
        print 'need edges: %s' % name

def latlongdist(x, y):
    # TODO: https://en.wikipedia.org/wiki/Haversine_formula
    return sqrt((abs(x['lat'] - y['lat'])**2) +
                (abs(x['long'] - y['long'])**2))

def latlongdist_walking(x, y):
    # walking along streets is much more like right angles than as-the-crow-flies direct routes...
    return (abs(x['lat'] - y['lat']) +
            abs(x['long'] - y['long']))

def stations_nearest(latlong):
    return [x for x, y in
                sorted([x for x in SubwayStations['Station'].items()
                    if x[1]['loc']['lat'] != 0.0 and x[1]['loc']['long'] != 0.0],
                  key=lambda x: latlongdist(latlong, x[1]['loc']),
                  reverse=False)[:20]]

def latlong2station((lat, long_)):
    return stations_nearest({'lat': lat,
                             'long': long_})

def shortest_path(g, source=None, target=None):
    try:
        return nx.shortest_path(g, source=source, target=target)
    except nx.exception.NetworkXNoPath:
        return []

def avg_walk_speed_mps():
    # ref: https://en.wikipedia.org/wiki/Preferred_walking_speed
    return 1.4

def time_to_walk_in_seconds(meters):
    return avg_walk_speed_mps() * meters

def latlongdist_to_meters(latlongdiff):
    return latlongdiff * 111111.0

def time_subway_speed_over_dist_mps(meters):
    # TODO: take a real guess
    # a better guess would take distance into account and the speed and brake curves...
    return meters / 15 # FIXME: real guess

def time_avg_plus_line_changes(route):
    # given a route, calculate the time the route would take
    # walking is approximated on average walk speed
    # time between stations is approximated via avg train speed
    # switching lines inside a station complex is approximated
    raise NotImplementedError()

def sec_to_min(sec):
    minutes = int(sec / 60)
    seconds = int(sec - (minutes * 60))
    return '%d:%02d' % (minutes, seconds)

def zip3(x, y, z):
    xi, yi, zi = iter(x), iter(y), iter(z)
    while True:
        yield (next(xi), next(yi), next(zi))

class SubwayEdge(object):
    def __init__(self, st1, st2):
        self.st1 = st1
        self.st2 = st2
        self.distance = self.station_distance()
        self.lines = set(SubwayGraphX[self.st1][self.st2].keys())
    def __repr__(self):
        return '%-9s %s --> %s dist=%.3f' % (
            '/'.join(sorted(self.lines)), self.st1, self.st2, self.distance)
    def station_distance(self):
        dist = latlongdist(SubwayStations['Station'][self.st1]['loc'],
                           SubwayStations['Station'][self.st2]['loc'])
        if dist > 1.0:
            print 'TOO FAR: distance between', st1, 'and', st2, 'is', dist
        return dist

class SubwayTrip(object):
    def __init__(self, st1, st2, start, goal):
        self.st1 = st1
        self.st2 = st2
        self.start = start
        self.goal = goal
        self.path = shortest_path(SubwayGraphX, source=st1, target=st2)
        self.route = list(starmap(SubwayEdge, zip(self.path, self.path[1:])))
        self.distance = sum(x.distance for x in self.route)
        self.min_line_changes = (sum(not (x.lines & y.lines)
                                        for x, y in zip(self.route,
                                                        self.route[1:])) +
                                 sum(bool(((x.lines & y.lines) and
                                           (y.lines & z.lines) and
                                            not (x.lines & z.lines)))
                                         for x, y, z in zip3(self.route,
                                                             self.route[1:],
                                                             self.route[2:])))
    def __eq__(self, other):
        return self.path == other.path
    def __repr__(self):
        return 'SubwayTrip(%s)' % self.route
    def time_avg(self):
        # given a route, calculate the average time between all points
        # walking is approximated on average walk speed
        # time between stations is approximated via avg train speed
        # switching lines inside a station complex is approximated
        st1 = SubwayStations['Station'][self.st1]
        st2 = SubwayStations['Station'][self.st2]
        self.dist_walk_to_first = latlongdist_walking(self.start, st1['loc'])
        time_walk_to_first = time_to_walk_in_seconds(latlongdist_to_meters(self.dist_walk_to_first))
        self.dist_walk_from_last = latlongdist_walking(st2['loc'], self.goal)
        time_walk_from_last = time_to_walk_in_seconds(latlongdist_to_meters(self.dist_walk_from_last))
        dist_between_stations = sum(x.station_distance() for x in self.route)
        time_between_stations =  time_subway_speed_over_dist_mps(latlongdist_to_meters(dist_between_stations))
        time_changing_lines = self.min_line_changes * 300
        return time_walk_to_first + time_between_stations + time_changing_lines + time_walk_from_last
    def format(self):
        print '    SubwayTrip (%s, %s, dist=%.3f, time_avg=%.1f, line_changes=%s)' % (
            self.st1, self.st2, self.distance, self.time_avg(), self.min_line_changes)
        print '        ', 'walk to %s dist=%.3f' % (self.st1, self.dist_walk_to_first)
        for edge in self.route:
            print '        ', edge
        print '        ', 'walk from %s dist=%.3f' % (self.st2, self.dist_walk_from_last)

def walking_distance_meters():
    return 1000

def walking_distance_latlong(latlongdist):
    return latlongdist_to_meters(latlongdist) < walking_distance_meters()

def stations_nearest_within_walking_distance(latlong, atleast=1, atmost=5):
    st = sorted((latlongdist(latlong, SubwayStations['Station'][x]['loc']), x)
                    for x in stations_nearest(latlong)[:atmost])
    return ([s for d, s in st[:atleast]] + \
            [s for d, s in takewhile(lambda (d, s): walking_distance_latlong(d), st[atleast:])])

class SubwayPossibilities(object):
    def __init__(self, start, goal):
        self.start = start
        self.goal = goal
        stations_nearest_start = stations_nearest_within_walking_distance(start, atleast=1, atmost=5)
        stations_nearest_goal = stations_nearest_within_walking_distance(goal, atleast=1, atmost=5)
        #pprint(stations_nearest_start, width=150)
        #pprint(stations_nearest_goal, width=150)
        self.trips = set(starmap(SubwayTrip, [(x, y, start, goal)
                                                for x, y in itertools.product(stations_nearest_start,
                                                                              stations_nearest_goal)]))
        self.trips = [y for x, y in sorted((x.time_avg(), x) for x in self.trips) if x if y.route]
    def __repr__(self):
        return 'SubwayPossibilities(n=%d, %s)' % (len(self.trips), self.trips)
    def format(self):
        print 'SubwayPossibilities(n=%d):' % len(self.trips)
        for t in self.trips:
            t.format()

class Trip(object):
    def __init__(self, start, goal):
        self.start = start
        self.goal = goal
        self.possibilities = SubwayPossibilities(start, goal)
    def __repr__(self):
        return 'Trip(%s --> %s, %s)' % (self.start, self.goal, self.possibilities)
    def format(self):
        print 'Trip %s --> %s' % (self.start, self.goal)
        self.possibilities.format()

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
    _125_St = {'lat': 40.804259, 'long': -73.937473}
    _Columbus_Circle = {'lat': 40.767997, 'long': -73.981934}

    print '--------------'

    #t = Trip(_171_Stanhope, _80_Broad_St)
    t = Trip(_80_Broad_St, _125_St)
    #t = Trip(_80_Broad_St, _Columbus_Circle)

    t.format()

    '''

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
    '''

    '''
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

    '''
    print ''
    pprint(nx.all_pairs_shortest_path(SubwayGraphX), width=150)
    '''
