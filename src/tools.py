# -*- coding:utf-8 -*-
import networkx as nx
import utm
import math
from shapely.geometry import Point, LineString

def pairwise(iterable):
    import itertools
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def outside(x, y, bounding_box):
    x0, x1, y0, y1 = bounding_box
    return x < x0 or x > x1 or y < y0 or y > y1