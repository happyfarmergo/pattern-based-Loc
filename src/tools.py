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

def bounding_box(coordinates):
    xs, ys = [], []
    for x, y in coordinates:
        xs.append(x)
        ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)

def accuracy(labels, y_predict):
    assert len(labels) == len(y_predict)
    cnt = 0
    for idx in range(len(labels)):
        if labels[idx] == y_predict[idx]:
            cnt += 1
    return cnt * 1.0 / len(labels)
