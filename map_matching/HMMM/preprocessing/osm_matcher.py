from .. import map_matching as mm
from ..map_matching.utils import Edge, Measurement
import sys
from geopy.distance import vincenty
from shapely.geometry import LineString
from rtree import index
import logging
from .. import mm_logger
import mm_parsing as mmp
import query_candiates as qcand
import cPickle
import re
import time
from ..map_matching.config import ALGORITHM
logger = logging.getLogger(mm_logger.APP_NAME)


def build_road_network(map_dir):
    '''
        build road network from reformated osm map.
    '''
    city_edges, city_edgeGeometry = mmp.getEdges(map_dir)
    logger.info('Size of edges: '+str(len(city_edges)))
    logger.info('Size of edgeGeometry: '+str(len(city_edgeGeometry)))

    graph, rt_idx = {}, index.Index()
    for rid, x, y, c in city_edges:
        edge = Edge(id=rid,
                    start_node=x,
                    end_node=y,
                    cost=c,
                    reverse_cost=c)
        city_edgeGeometry[rid][0] = edge
        rt_idx.insert(rid, city_edgeGeometry[rid][1].bounds)
        graph.setdefault(edge.start_node, []).append(edge)
        graph.setdefault(edge.end_node, [])

    # cPickle.dump(graph,open("test\\graph.pkl_","wb"))
    # cPickle.dump(rt_idx,open("test\\rt_idx.pkl_","wb"))
    # cPickle.dump(city_edgeGeometry,open("test\\city_edgeGeometry.pkl_","wb"))
    #graph = cPickle.load(open("test\\graph.pkl_","rb"))
    #rt_idx = cPickle.load(open("test\\rt_idx.pkl_","rb"))
    #city_edgeGeometry = cPickle.load(open("test\\city_edgeGeometry.pkl_","rb"))
    return graph, rt_idx, city_edgeGeometry



def match_one(network, sequence, time_gap, rt_idx, city_edgeGeometry, search_radius, max_route_distance):
    start_time = time.time()
    dist = search_radius
    cut_idxs = [m.start() for m in re.finditer('/', sequence)]
    out_folder = sequence[:cut_idxs[-2]] + '/matching_out' + sequence[cut_idxs[-1]:]
    logger.info('Output folder: ' + out_folder)
    # found candidates for each GPS point
    candidates = qcand.calc(sequence, time_gap, rt_idx, city_edgeGeometry, search_radius)
    # logger.debug('Size of candies: ' + str(len(candidates)))
    # If the route distance between two consive measurements are
    # longer than `max_route_distance` in meters, consider it as a
    # breakage
    matcher = mm.MapMatching(network.get, max_route_distance)
    candies = list(matcher.offline_match(candidates))
    end_time = time.time()
    logger.info('Out len of trajectory: '+ str(len(candies)))
    with open(out_folder+'.'+ ALGORITHM.name + '.G_gap='+str(time_gap)+'_dist='+str(dist)+'.txt', 'w') as fout:
        for idx, candidate in enumerate(candies):
            outline = [candidate.measurement.id, \
                    candidate.measurement.lat, \
                    candidate.measurement.lon, \
                    candidate.edge.id, \
                    candidate.lat, candidate.lon, \
                    candidate.location, \
                    candidate.distance]
            if idx > 0 and candies[idx-1] in candidate.path:
                candidate.path[candies[idx - 1]].reverse()
                for seg in candidate.path[candies[idx - 1]]:
                    if seg.id == candies[idx - 1].edge.id:
                        continue
                    if seg.id == candidate.edge.id:
                        break
                    comp_line = [candidate.measurement.id, \
                        candidate.measurement.lat, \
                        candidate.measurement.lon, \
                        seg.id,0,0,0,0
                        ]
                    print >> fout, ','.join(map(str,comp_line))
            print >> fout, ','.join(map(str,outline))
        print >> fout, 'Time_cost', end_time - start_time
def map_match(road_network, sequence, search_radius,time_gap, max_route_distance):
    """Match the sequence and return a list of candidates."""

    # Prepare the network graph and the candidates along the sequence
    network, rt_idx, city_edgeGeometry = build_road_network(road_network)
    if sequence.endswith('task_list'):
        with open(sequence) as tfin:
            for task in tfin.readlines():
                match_one(network, task.strip(), time_gap, rt_idx, city_edgeGeometry,search_radius,max_route_distance)
    else:
        match_one(network, sequence,time_gap, rt_idx, city_edgeGeometry,search_radius,max_route_distance)

def parse_argv(argv):
    argv = argv[:] + [None, None, None, None]
    try:
        road_network, sequence, alg_name, search_radius,time_gap, max_route_distance = argv[:6]
        if alg_name not in ['ST','HMM','FV']:
            print alg_name
            raise Exception('No such map matching algorithm')
        ALGORITHM.name = alg_name
        search_radius = 100 if search_radius is None else int(search_radius)
        time_gap = 1 if time_gap is None else int(time_gap)
        max_route_distance = 2000 if max_route_distance is None else int(max_route_distance)
    except ValueError:
        print >> sys.stderr, __doc__
        return

    return road_network, sequence, search_radius, time_gap, max_route_distance


def main(argv):
    params = parse_argv(argv)
    if not params:
        # Something is wrong
        return 1
    logger.info('Params: '+ str(params))
    road_network, sequence, search_radius, time_gap, max_route_distance = params
    map_match(road_network, sequence, search_radius,time_gap, max_route_distance)
    # for candidate in candidates:
    #     print '         Measurement ID: {0}'.format(candidate.measurement.id)
    #     print '             Coordinate: {0:.6f} {1:.6f}'.format(*map(float, (candidate.measurement.lon, candidate.measurement.lat)))
    #     print '    Matche d coordinate: {0:.6f} {1:.6f}'.format(*map(float, (candidate.lon, candidate.lat)))
    #     print '        Matched edge ID: {0}'.format(candidate.edge.id)
    #     print 'Location along the edge: {0:.2f}'.format(candidate.location)
    #     print '               Distance: {0:.2f} meters'.format(candidate.distance)
    #     print

    return 0
