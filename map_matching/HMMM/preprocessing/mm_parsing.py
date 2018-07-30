import logging
from geopy.distance import vincenty
from shapely.geometry import LineString
from .. import mm_logger

from datetime import datetime
from geopy.distance import vincenty
from collections import defaultdict
import time

logger = logging.getLogger(mm_logger.APP_NAME)


def calc_positions_distance(lats, lngs):
    '''
        lats: latitude list, lngs: longitude list
        calc the vincenty distance of a road edge.
    '''
    positions = zip(lats, lngs)
    distance = 0
    for i in range(1, len(positions)):
        distance += vincenty(positions[i-1], positions[i]).meters
    return distance


def parse_edges(city_edges_path):
    logger.info('Parsing edges: '+ city_edges_path)
    city_edges =[]
    with open(city_edges_path) as fcep:
        for line in fcep.readlines():
            rid, start_n, end_n = [int(_) for _  in line.split(' ')[:3]]
            cost = float(line.strip().split(' ')[-1])
            city_edges.append((rid, start_n, end_n, cost))
    return city_edges

def parse_edgeGeometry(city_edgeGeometry_path):
    '''
        city_edgeGeometry: [LineString([(longitude, latitude),...])]
    '''
    logger.info('Parsing edgeGeometry: '+ city_edgeGeometry_path)
    city_edgeGeometry = defaultdict(list)
    with open(city_edgeGeometry_path) as fceGp:
        for line in fceGp.readlines():
            arr = [float(_) for _ in line.strip().split('^')[4:]]
            lngs, lats = arr[1::2], arr[::2]
            rid = int(line.strip().split('^')[0])
            if len(lngs) <= 1:
                print rid
            city_edgeGeometry[rid]=[ None, LineString(zip(lngs, lats))]
    return city_edgeGeometry

def getEdges(map_dir):
    '''
        map_dir folder name should has the city name as prefix,
        {city}_Nodes.txt, {city}_Edges_cost.txt, {city}_EdgeGeometry.txt
        e.g. city = SH (Shanghai)
    '''
    if map_dir[-1] == '/': map_dir = map_dir[:-1]
    city = map_dir.split('/')[-1].split('_')[0]
    city_edges_path = map_dir + '/' +city + '_Edges.txt'
    city_edgeGeometry_path = map_dir + '/' + city + '_EdgeGeometry.txt'

    return parse_edges(city_edges_path), parse_edgeGeometry(city_edgeGeometry_path)

def string_toDatetime(string):
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def string_toTimestamp(strTime):
    return int(time.mktime(string_toDatetime(strTime).timetuple()))

def tuple_3_txt(columns):
    timstp = int(columns[0])
    lat, lng = [float(_) for _ in columns[1:]]
    return timstp, lat, lng

def tuple_13_txt(columns):
    timstp = string_toTimestamp(columns[7])
    lng = float(columns[8])
    lat = float(columns[9])
    return timstp, lat, lng

def parsing_line(line):
    cols = line.strip().split(',')
    if len(cols) == 3:
        return tuple_3_txt(cols)
    else:
        if len(cols) == 13:
            return tuple_13_txt(cols)

def getTrajectory(sequence, time_gap):
    logger.info('Parsing trajectory: '+ sequence)
    '''
        trajecory = [(timestamp, latitude, longitude), ... ]
    '''
    trajectory = []
    with open(sequence) as fseq:
        st_time = 0
        dlines = fseq.readlines()
        for idx, line in enumerate(dlines):
            timstp, lat, lng = parsing_line(line)
#            if idx == len(dlines)-1 or timstp - st_time >= time_gap:
#                gap = timstp - st_time
#                if st_time == 0:
#                    gap == 1
#                trajectory.append((timstp, lat, lng, gap))
#                st_time = timstp
            gap = timstp - st_time
            if st_time == 0:
                gap == 1
            trajectory.append((timstp, lat, lng, gap))
            st_time = timstp

    logger.info('len of trajectory: '+ str(len(trajectory)))
    return trajectory
