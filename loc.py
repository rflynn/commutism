#!/usr/bin/env python2.7
# vim: set ts=4 et:

from math import sqrt
from pprint import pprint
from itertools import takewhile, dropwhile, groupby, starmap
from collections import defaultdict

# TODO: cutoff "stupid" paths that involve walking out and then taking the train back to where you started

try:
    import networkx as nx
except ImportError:
    # pypy needs this
    import sys
    sys.path.insert(0, './venv/lib/python2.7/site-packages')
    import networkx as nx

import yaml

SubwayStations = dict()
with open('./data/ref/nyc-subway-station-complexes-2013.yml') as f:
    SubwayStations = yaml.load(f)

SubwayGraphX = nx.MultiDiGraph()

print 'needs edges:', # remind self of incomplete graph data...
# build digraphs for each line
for name, station in SubwayStations['Station'].iteritems():
    if 'edges' in station:
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
        print '%s,' % name.rstrip(),
print ''

# TODO: add the ability to extract individual lines out as diffs, then add them back in

# override-able settings on a per-person basis with sane defaults
class PersonalProfile(object):
    def __init__(self):
        # ref: https://en.wikipedia.org/wiki/Preferred_walking_speed
        self.walking_speed_mps = 1.4
        self.walking_distance_meters = 1000

class AggressiveWalkerProfile(PersonalProfile):
    def __init__(self):
        super(AggressiveWalkerProfile, self).__init__()
        self.walking_speed_mps = 2.1
        self.walking_distance_meters = 1500

def latlongdist(x, y):
    # TODO: https://en.wikipedia.org/wiki/Haversine_formula
    return sqrt((abs(x['lat'] - y['lat'])**2) +
                (abs(x['long'] - y['long'])**2))

def latlongdist_walking(x, y):
    return latlongdist(x, y) * 1.3
    # FIXME: assuming right angles for everything is actually not the best way to go, as NYC
    # is not laid out in a strictly N/S/E/W grid...
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

def time_to_walk_in_seconds(person, meters):
    # TODO: separate horizontal and vertical walking...
    return meters / person.walking_speed_mps

def latlongdist_to_meters(latlongdiff):
    # TODO: improve this rough approximation
    return latlongdiff * 111111.0

def time_subway_speed_over_dist_mps(meters):
    # TODO: take a real guess
    # a better guess would take distance into account and the speed and brake curves...
    if meters < 1000: return meters / 5
    return (1000 / 5) + ((meters - 500) / 15)
    #return meters / 15 # ~34 mph # FIXME: real guess

def time_bus_speed_over_dist_mps(meters):
    # TODO: take a real guess
    # a better guess would take distance into account and the speed and brake curves...
    return meters / 9 # ~20 mph # FIXME: real guess

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
        return '%-9s %s -> %s dist=%.3f' % (
            '/'.join(sorted(self.lines)), self.st1, self.st2, self.distance)
    def condensed(self):
        return '%s -> %s' % (self.st1, self.st2)
    def station_distance(self):
        dist = latlongdist(SubwayStations['Station'][self.st1]['loc'],
                           SubwayStations['Station'][self.st2]['loc'])
        if dist > 1.0:
            print 'TOO FAR: distance between', self.st1, 'and', self.st2, 'is', dist
        return dist
    @staticmethod
    def stationlist(edges):
        if not edges:
            return []
        if len(edges) == 1:
            return [edges[0].st1, edges[0].st2]
        return [edges[0].st1] + [e.st2 for e in edges[1:]]
    @staticmethod
    def first_and_last(edges):
        if not edges:
            return None
        if len(edges) == 1:
            return (edges[0].st1, edges[0].st2)
        return (edges[0].st1, edges[-1].st2)
    @staticmethod
    def vertical_cost_of_switching_lines(lfrom, lto, station_name):
        # transferring from lfrom -> to, how many floors are in-between?
        station = SubwayStations['Station'][station_name]
        lfrom1 = list(lfrom)[0]
        lto1 = list(lto)[0]
        linefloormap = SubwayEdge.lines_to_station_floors(station)
        if not linefloormap:
            return None
        fromlevel = station['layout'][list(linefloormap[lfrom1])[0]].get('level')
        tolevel = station['layout'][list(linefloormap[lto1])[0]].get('level')
        if fromlevel is None or tolevel is None:
            return None
        return abs(tolevel - fromlevel) # TODO: separate going up from going down
    @staticmethod
    def lines_to_station_floors(station):
        # given a set of lines and a station.layout, map the lines to the floors
        station = station or dict()
        if not station.get('layout'):
            return None
        #print 'station:', station
        y = [[(k,f) for k in l.keys()]
                for f,l in [(floor, lines.get('lines', {}) if lines else {})
                    for floor, lines in station.get('layout',{}).items()
                        ]]
        d = defaultdict(set)
        for floorlines in y:
            for line, floor in floorlines:
                d[line].add(floor)
        return dict(d)

class SubwayTrip(object):
    def __init__(self, person, path, start, goal):
        self.person = person
        self.st1 = path[0]
        self.st2 = path[-1]
        self.start = start
        self.goal = goal
        self.path = path
        self.route = list(starmap(SubwayEdge, zip(self.path, self.path[1:])))
        self.distance = sum(x.distance for x in self.route)
        self.route_by_line = self.calc_lines()
        self.line_change_count = len(self.route_by_line) - 1

    def calc_lines(self):
        # given a possibly ambiguous route, converge contiguous runs of the same line
        # [(line, edges), ...]
        lines = [(l, list(e))
                    for l, e in groupby(self.route,
                                        lambda e: e.lines)]
        lg = []
        while lines:
            # segment route into contiguous runs of the same line, and swallow dupes
            line, edges = lines.pop(0)
            while lines and line & lines[0][0]:
                l, e = lines.pop(0)
                line = line & l
                edges.extend(e)
            lg.append((line, edges))
        return lg

    def __eq__(self, other):
        return self.path == other.path
    def __repr__(self):
        return 'SubwayTrip(%s)' % self.route
    def time_avg(self):
        # given a route, calculate the average time between all points
        # walking is approximated on average walk speed
        # time between stations is approximated via avg train speed
        # switching lines inside a station complex is approximated
        # TODO: treat out-of-system transfers as walking, not subway speed...
        st1 = SubwayStations['Station'][self.st1]
        st2 = SubwayStations['Station'][self.st2]
        self.dist_walk_to_first = latlongdist_walking(self.start, st1['loc'])
        time_walk_to_first = time_to_walk_in_seconds(self.person,
                                                     latlongdist_to_meters(self.dist_walk_to_first))
        if st1.get('elevated'):
            time_walk_to_first += 60 # FIXME: hack
        self.dist_walk_from_last = latlongdist_walking(st2['loc'], self.goal)
        time_walk_from_last = time_to_walk_in_seconds(self.person,
                                                      latlongdist_to_meters(self.dist_walk_from_last))
        dist_between_stations = sum(x.station_distance() for x in self.route)
        time_between_stations = (
            time_subway_speed_over_dist_mps(latlongdist_to_meters(dist_between_stations))
            + (len(self.route) * 30) # stops in station
        )
        time_changing_lines = self.line_change_count * 360
        # TODO: save this data to an intermediary data structure so we can display a line item
        time_changing_stations = self.time_changing_stations()
        return (
            time_walk_to_first
            + time_between_stations
            + time_changing_stations
            + time_changing_lines
            + time_walk_from_last
        )
    def time_changing_stations(self):
        # take into account transfer cost within stations between lines
        # TODO: take cost of walking up/down to first stations...
        # on same line...
        firstandlasts = [(line, stations[0], stations[-1])
                            for line, stations in self.route_by_line]
        transfers = [(x[0], y[0], x[2].st2)
                        for x, y in zip(firstandlasts,
                                        firstandlasts[1:])]
        #print 'transfers:', transfers
        costs = starmap(SubwayEdge.vertical_cost_of_switching_lines, transfers)
        # 60 seconds per floor
        return sum((c or 0) * 60 for c in costs)

    def format(self, condensed=False):
        print '    SubwayTrip (%s, %s, dist=%.3f, time_avg=%s, line_changes=%s)' % (
            self.st1, self.st2, self.distance, sec_to_min(self.time_avg()), self.line_change_count)
        print '        ', 'walk to %s dist=%.3f time=%s' % (self.st1, self.dist_walk_to_first,
            sec_to_min(time_to_walk_in_seconds(self.person,
                                               latlongdist_to_meters(self.dist_walk_to_first))))
        if condensed:
            for lines, edges in self.route_by_line:
                first, last = SubwayEdge.first_and_last(edges)
                print '         %-9s %s -> %s' % ('/'.join(sorted(lines)), first, last)
        else:
            for edge in self.route:
                print '        ', edge
        print '        ', 'walk from %s dist=%.3f times=%s' % (self.st2, self.dist_walk_from_last,
            sec_to_min(time_to_walk_in_seconds(self.person,
                                               latlongdist_to_meters(self.dist_walk_from_last))))

def walking_distance_meters():
    return 1500

def walking_distance_latlong(latlongdist):
    return latlongdist_to_meters(latlongdist) < walking_distance_meters()

def stations_nearest_within_walking_distance(latlong, atleast=1, atmost=5):
    st = sorted((latlongdist(latlong, SubwayStations['Station'][x]['loc']), x)
                    for x in stations_nearest(latlong)[:atmost])
    return ([s for d, s in st[:atleast]] + \
            [s for d, s in takewhile(lambda (d, s): walking_distance_latlong(d), st[atleast:])])

class SubwayPossibilities(object):
    def __init__(self, person, start, goal):
        self.person = person
        self.start = start
        self.goal = goal
        stations_nearest_start = stations_nearest_within_walking_distance(start, atleast=1, atmost=8)
        # TODO: the farther away from the goal our start is, the less it's worth optimizing the starting point...
        pprint(stations_nearest_start, width=150)
        stations_nearest_goal = stations_nearest_within_walking_distance(goal, atleast=1, atmost=8)
        pprint(stations_nearest_goal, width=150)
        self.trips = set(starmap(SubwayTrip,
            [(person, list(path), start, goal)
                for x, y in itertools.product(stations_nearest_start,
                                              stations_nearest_goal)
                    for path in set(map(tuple,
                        list(nx.all_simple_paths(SubwayGraphX, source=x,
                                                          target=y,
                                                          cutoff=11)) + \
                        [shortest_path(SubwayGraphX, source=x,
                                                    target=y)])) if path]))
        self.trips = [y for x, y in
                        sorted((x.time_avg(), x)
                            for x in self.trips) if x if y.route]
    def __repr__(self):
        return 'SubwayPossibilities(n=%d, %s)' % (len(self.trips), self.trips)
    def format(self, condensed=False):
        print 'SubwayPossibilities(n=%d):' % len(self.trips)
        for t in self.trips:
            t.format(condensed=condensed)

# TODO: taxi! uber!
class Trip(object):
    def __init__(self, person, start, goal):
        self.person = person
        self.start = start
        self.goal = goal
        self.possibilities = SubwayPossibilities(person, start, goal)
    def __repr__(self):
        return 'Trip(%s -> %s, %s)' % (self.start, self.goal, self.possibilities)
    def format(self, condensed=False):
        print 'Trip %s -> %s' % (self.start, self.goal)
        self.possibilities.format(condensed=condensed)

if __name__ == '__main__':

    import sys
    import itertools

    #print latlong2station((0., 0.))
    #print latlong2station((-73.976522, 40.7528))
    #print latlong2station((-73.97652, 40.752))
    #print latlong2station((-73.9765, 40.752))
    #print latlong2station((-73.976, 40.752))
    #print latlong2station((40.75, -73.97))
    #print latlong2station((40.704294, -73.919277)) # DeKalb (L)
    #print latlong2station((40.699377, -73.922061)) # 171 Stanhope
    #print latlong2station((40.704283, -74.011963)) # 80 Broad St
    _171_Stanhope = {'lat': 40.699377, 'long': -73.922061}
    _80_Broad_St = {'lat': 40.704283, 'long': -74.011963}
    _125_St = {'lat': 40.804259, 'long': -73.937473}
    _Columbus_Circle = {'lat': 40.767997, 'long': -73.981934}
    _Court_Sq = {'lat': 40.747615, 'long': -73.945069}
    _Astoria_Blvd = {'lat': 40.769979, 'long': -73.918161}
    _Queensboro_Plaza = {'lat': 40.750653, 'long': -73.940344}
    Queens_Plaza = {'lat': 40.748915, 'long': -73.937387}
    _36_Av = {'lat': 40.756555, 'long': -73.929791}
    _LaGuardia = {'lat': 40.77725, 'long': -73.872611}
    _Lorimer_Met_Av = {'lat': 40.712752, 'long': -73.951464}
    Times_Sq = {'lat': 40.756, 'long': -73.987}
    _Lexington_Av = {'lat': 40.762471, 'long': -73.9679}
    _49_St = {'lat': 40.760423, 'long': -73.983779}
    _ResortsWorld = {'lat': 40.672663, 'long': -73.832625}
    _MyrtleAv = {'lat': 40.696941, 'long': -73.935285}

    _GatesAv = {'lat': 40.68949, 'long': -73.922067}
    _ChaunceySt = {'lat': 40.682623, 'long': -73.910136}

    KosciuszkoSt = {'lat': 40.693167, 'long': -73.928633}

    BryantPark = {'lat': 40.754799, 'long': -73.984208}
    BarclaysCtr = {'lat': 40.684462, 'long': -73.978758}
    ChurchAvBQ = {'lat': 40.64966, 'long': -73.963646}
    ProspectPark = {'lat': 40.661507, 'long': -73.962461}
    BrightonBeach = {'lat': 40.577598, 'long': -73.961565}
    _7AvBQ = {'lat': 40.679352, 'long': -73.973694}

    Foresthills71Av = {'lat': 40.721404, 'long': -73.844004}
    Jamaica_179_St = {'lat': 40.712459, 'long': -73.78448}
    _121_St = {'lat': 40.700357, 'long': -73.82894}
    Broadway_Junction = {'lat': 40.678919, 'long': -73.903453}

    Crescent_St = {'lat': 40.683665, 'long': -73.872414}

    Woodhaven_Blvd_JZ = {'lat': 40.693622, 'long': -73.852158}
    _75_Av = {'lat': 40.71864, 'long': -73.837738}
    Sutphin_Blvd_Archer_Av_JFK_Airport = {'lat': 40.700488, 'long': -73.80774}

    Grand_Central = {'lat': 40.7528, 'long': -73.976522}

    Parkchester = {'lat': 40.832937, 'long': -73.862758}

    Hoboken_Terminal = {'lat': 40.7349, 'long': -74.0278}

    Graham_Av = {'lat': 40.714509, 'long': -73.944426}

    Franklin_Av = {'lat': 40.681126, 'long': -73.955712}

    South_Ferry = {'lat': 40.702472, 'long': -74.012833}

    Lafayette_Av = {'lat': 40.686268, 'long': -73.974466}
    Court_St_Borough_Hall = {'lat': 40.693655, 'long': -73.990216}


    print '--------------'

    #p = AggressiveWalkerProfile()
    p = PersonalProfile()

    t = Trip(p, _171_Stanhope, _80_Broad_St)
    #t = Trip(p, _80_Broad_St, _171_Stanhope)
    #t = Trip(p, _80_Broad_St, _125_St)
    #t = Trip(p, _171_Stanhope, _125_St)
    #t = Trip(p, _80_Broad_St, _Columbus_Circle)
    #t = Trip(p, _Court_Sq, _125_St)
    #t = Trip(p, _Astoria_Blvd, _125_St)
    #t = Trip(p, _Queensboro_Plaza, _80_Broad_St)
    #t = Trip(p, Queens_Plaza, _80_Broad_St)

    #t = Trip(p, _36_Av, _125_St)
    #t = Trip(p, _171_Stanhope, _LaGuardia)
    #t = Trip(p, _171_Stanhope, _125_St)
    #t = Trip(p, _125_St, _LaGuardia)
    #t = Trip(p, _171_Stanhope, _Court_Sq)
    #t = Trip(p, _171_Stanhope, _Lorimer_Met_Av)
    #t = Trip(p, _Lorimer_Met_Av, _Court_Sq)
    #t = Trip(p, Times_Sq, _LaGuardia)
    #t = Trip(p, _Lexington_Av, _LaGuardia)
    #t = Trip(p, _49_St, _Lexington_Av)
    #t = Trip(p, _49_St, _LaGuardia)
    #t = Trip(p, _171_Stanhope, _ResortsWorld)
    #t = Trip(p, _MyrtleAv, _ResortsWorld)
    #t = Trip(p, _GatesAv, _ResortsWorld)
    #t = Trip(p, _ChaunceySt, _ResortsWorld)
    #t = Trip(p, KosciuszkoSt, _ResortsWorld)
    #t = Trip(p, BarclaysCtr, BrightonBeach)
    #t = Trip(p, BryantPark, BarclaysCtr)
    #t = Trip(p, BryantPark, BrightonBeach)

    #t = Trip(p, Jamaica_179_St, _80_Broad_St) # FIXME: too slow, needs cutoff=15 since our graph is overly simplified as station-to-station when it should be based on line. ah well..
    #t = Trip(p, _75_Av, _80_Broad_St)

    #t = Trip(p, _121_St, _80_Broad_St)
    #t = Trip(p, _121_St, Broadway_Junction)
    #t = Trip(p, Crescent_St, Broadway_Junction)
    #t = Trip(p, _121_St, Woodhaven_Blvd_JZ) # works
    #t = Trip(p, Woodhaven_Blvd_JZ, Crescent_St) # one stop

    #t = Trip(p, Sutphin_Blvd_Archer_Av_JFK_Airport, _80_Broad_St)
    #t = Trip(p, Woodhaven_Blvd_JZ, _80_Broad_St)

    #t = Trip(p, Times_Sq, _80_Broad_St)
    #t = Trip(p, Parkchester, _80_Broad_St)

    #t = Trip(p, Hoboken_Terminal, _80_Broad_St)

    #t = Trip(p, Foresthills71Av, _80_Broad_St)
    #t = Trip(p, _80_Broad_St, Foresthills71Av)
    #t = Trip(p, _80_Broad_St, Graham_Av)

    #t = Trip(p, Franklin_Av, _80_Broad_St)
    #t = Trip(p, Franklin_Av, _ResortsWorld)
    #t = Trip(p, Lafayette_Av, Court_St_Borough_Hall)
    #t = Trip(p, Franklin_Av, South_Ferry)

    Atlantic_Av_Barclays_Ctr = {
        'lat': 40.684462,
        'long': -73.978758
    }
    Bay_Ridge_95_St = {'lat': 40.615667, 'long': -74.031361}
    t = Trip(p, Atlantic_Av_Barclays_Ctr, Bay_Ridge_95_St)

    t.format(condensed=True)

