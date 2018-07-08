import numpy as np
import pandas as pd
import utm
import math
import pickle
import os
import sys
import time
import datetime
from collections import defaultdict
import matplotlib
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from itertools import chain
import copy

import tools

def accuracy(labels, y_predict):
    assert len(labels) == len(y_predict)
    cnt = 0
    for idx in range(len(labels)):
        if labels[idx] == y_predict[idx]:
            cnt += 1
    return cnt * 1.0 / len(labels)

def retrive_per_window(df, grid, towers, start, w_size):
    grids = []
    features = []
    if start + w_size - 1 > df.index[-1]:
        return features, grids
    for i in range(start, start + w_size):
        piece_data = df.loc[i]
        lat, lng = piece_data['Latitude'], piece_data['Longitude']
        x, y, _, _ = utm.from_latlon(lat, lng)
        cid = grid.utm2cell(x, y)
        grids.append(cid)
        
        piece_ids = []
        for idx in range(1, 7 + 1):
            rncid, cellid = piece_data['RNCID_%d'%idx], piece_data['CellID_%d'%idx]
            index_id = towers[(rncid, cellid)][0] if (rncid, cellid) in towers.keys() else -1
            piece_ids.append(index_id)
        features.append(piece_ids)
    return features, grids

def retrive(df, grid, towers, w_size):
    total_pattern, total_feature = [], []
    statistic = []
    max_trid = max(df['TrajID'])
    for traj_id in range(max_trid + 1):
        print('TrajID=' + str(traj_id))
        df_traj = df[df['TrajID']==traj_id]
        # for start in range(df_traj.index[0], df_traj.index[-1], w_size):
        for start in df_traj.index:
            features, grid_pattern = retrive_per_window(df_traj, grid, towers, start, w_size)
            if len(grid_pattern) == 0:
                break
            total_pattern.append(grid_pattern)
            total_feature.append(features)
            x0, x1, y0, y1 = grid.boxsize(grid_pattern)
            statistic.append((x1 - x0, y1 - y0))
    return total_feature, total_pattern, pd.DataFrame(statistic, columns=['width', 'height'])

def pattern2label(patterns, grid, version=0):
    if version == 0:
        labels = []
        for pattern in patterns:
            t_vx, t_vy = 0, 0
            for c1, c2 in tools.pairwise(pattern):
                vx, vy = grid.cell_vec(c1, c2)
                t_vx += vx
                t_vy += vy
            labels.append((t_vx, t_vy))
    elif version == 1:
        new_patterns = []
        for pattern in patterns:
            temp = [grid.cell2index(cid) for cid in pattern]
            xs = [idx[0] for idx in temp]
            ys = [idx[1] for idx in temp]
            x0, y0 = min(xs), min(ys)
            new_pattern = []
            for idx in temp:
                new_pattern.append(idx[0] - x0)
                new_pattern.append(idx[1] - y0)
            new_patterns.append(tuple(new_pattern))
        pattern_set = list(set(new_patterns))
        labels = [pattern_set.index(pattern) for pattern in new_patterns]
    return labels

def cellids2feature(cellids, version=0):
    features = []
    for cellid in cellids:
        if version == 0:
            features.append(list(chain.from_iterable(cellid)))
    return features