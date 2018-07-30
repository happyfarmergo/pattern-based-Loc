from geopy.distance import vincenty
from shapely.geometry import LineString, Point
from rtree import index
from .. import map_matching as mm
from ..map_matching.utils import Edge, Measurement
import mm_parsing as mmp
import geopy
import geopy.distance
from .. import mm_logger
import logging
logger = logging.getLogger(mm_logger.APP_NAME)

# Subclass the native Candidate class to support more attributes
class Candidate(mm.Candidate):
    def __init__(self, measurement, edge, location, distance):
        super(Candidate, self).__init__(measurement=measurement, edge=edge, location=location, distance=distance)
        self.lon = None
        self.lat = None

# https://stackoverflow.com/questions/24427828/calculate-point-based-on-distance-and-direction
def get_minimum_rectangle(lat, lng, search_radius):
    import math
    # Define the diagonal length from center to
    # bottom-left (Southwest) and
    # up-right (Northeast) point.
    diag_len = search_radius * math.sqrt(2)
    center = geopy.Point(lat, lng)
    # Define a distance object, initialized with a distance of diag_len m.(about 42.4m
    # when search_radius is 30m)
    vinc_diag_len = geopy.distance.VincentyDistance(meters = diag_len)
    # Use the `destination` method with a bearing of 0 degrees (which is north)
    # 45 degree is Northeast, 225 degree is Southwest
    # in order to go from point `start` 1 km to north.
    northeast = vinc_diag_len.destination(point = center, bearing = 45)
    southwest = vinc_diag_len.destination(point = center, bearing = 225)

    return southwest.longitude,\
            southwest.latitude,\
            northeast.longitude,\
            northeast.latitude

def candy_retrieve(timstp, lat, lng, gap, rt_idx, city_edgeGeometry, search_radius):
    search_bounds = get_minimum_rectangle(lat, lng, search_radius)
    loose_candies = list(rt_idx.intersection(search_bounds))
    gps_point = Point(lng, lat)
    found_candy = False
    for candy in loose_candies:
        line = city_edgeGeometry[candy][1]
        location = line.project(gps_point, True)
        if location == 0:
            location = 0.0001
        if location == 1:
            location = 0.9999
        proj_point = line.interpolate(location, True)
        real_distance = vincenty((lat, lng), (proj_point.y, proj_point.x)).meters
        if real_distance <= search_radius:
            found_candy = True
            measurement = Measurement(id=timstp, lon=lng, lat=lat)
            edge = city_edgeGeometry[candy][0]
            assert 0 <= location <= 1
            candidate = Candidate(measurement=measurement, edge=edge, location=location, distance=real_distance)
            candidate.interval = gap
            candidate.lat = proj_point.y
            candidate.lon = proj_point.x
            yield candidate
    if not found_candy:
        logger.info('Point missing: '+ str(timstp)+' '+ str(lat)+ ',' +str(lng))



def calc( sequence, time_gap, rt_idx, city_edgeGeometry, search_radius):
    '''
        calc the candidates of each gps point in trajectory.
        rt_idx: rtree index of roads
        city_edgeGeometry: list of shapely.geometry.LinesString represent a road
        search_radius: we use a minumum rectangle contain this search circle for retrieving road from rtree.
    '''
    trajecory = mmp.getTrajectory(sequence, time_gap)

    for timstp, lat, lng, gap in trajecory:
        for candy in candy_retrieve(timstp, lat, lng, gap, rt_idx, city_edgeGeometry, search_radius):
            yield candy

