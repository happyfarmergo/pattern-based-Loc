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

def retrive_next_window(df, grid, towers, edgemap, nodemap, start, w_size):
    pass

def retrive_per_window(df, grid, towers, edgemap, nodemap, start, w_size):
    grids, features, grid_pattern = [], [], []
    last_edge_id = -1
    for i in range(start, start + w_size):
        piece_data = df.loc[i]
        x, y, edge_id = piece_data['Match_UTM_X'], piece_data['Match_UTM_Y'], piece_data['RoadID']
        # print (edge_id)
        # error data
        if last_edge_id != -1 and last_edge_id != edge_id:
            st1, et1 = edgemap[last_edge_id]
            if st1 not in edgemap[edge_id] and et1 not in edgemap[edge_id]:
                grids, features, grid_pattern = [], [], []
                # print ('-----------Cut Down Edge------------')
                break
            else:
                nodeid = st1 if st1 in edgemap[edge_id] else et1
                lat, lng = nodemap[nodeid]
                x, y, _, _ = utm.from_latlon(lat, lng)
                grid_pattern.append((x, y))
                grids.append(grid.utm2cell(x, y))
        cid = grid.utm2cell(x, y)
        grids.append(cid)
        grid_pattern.append((x, y))
        
        piece_ids = []
        for idx in range(1, 7 + 1):
            rncid, cellid, rssi = int(piece_data['RNCID_%d'%idx]), int(piece_data['CellID_%d'%idx]), int(piece_data['Dbm_%d'%idx])
            index_id = towers[(rncid, cellid)][0] if (rncid, cellid) in towers.keys() else -1
            # if index_id != -1:
            #     lat, lng = towers[(rncid, cellid)][1], towers[(rncid, cellid)][2]
            # else:
            #     lat, lng = 0, 0
            # piece_ids.append((index_id, lat, lng, rssi))
            piece_ids.append(index_id)
        features.append(piece_ids)
        last_edge_id = edge_id
    return features, grids, grid_pattern

def retrive(df, grid, towers, edgemap, nodemap, w_size):
    total_pattern, total_feature = [], []
    statistic = []
    max_trid = max(df['TrajID'])
    for traj_id in range(max_trid + 1):
        # print('TrajID=' + str(traj_id))
        df_traj = df[df['TrajID']==traj_id]
        # for start in range(df_traj.index[0], df_traj.index[-1], w_size):
        for start in df_traj.index:
            if start + w_size - 1 > df_traj.index[-1]:
                break
            # print ('Window %s' % start)
            features, grids, grid_pattern = retrive_per_window(df_traj, grid, towers, edgemap, nodemap, start, w_size)
            if len(grid_pattern) == 0:
                continue
            total_pattern.append(grid_pattern)
            total_feature.append(features)
            x0, x1, y0, y1 = grid.boxsize(grids)
            statistic.append((x1 - x0, y1 - y0))
    return total_feature, total_pattern, pd.DataFrame(statistic, columns=['width', 'height'])


def decide_label(x, y):
    if x < 0 and y > 0:
        new_label = 1
    elif x == 0 and y > 0:
        new_label = 2
    elif x > 0 and y > 0:
        new_label = 3
    elif x > 0 and y == 0:
        new_label = 4
    elif x > 0 and y < 0:
        new_label = 5
    elif x == 0 and y < 0:
        new_label = 6
    elif x < 0 and y < 0:
        new_label = 7
    elif x < 0 and y == 0:
        new_label = 8
    elif x == 0 and y == 0:
        new_label = 0
    return new_label

# def decide_label(x, y, c_angle=15):
#     if x == 0.0 and y == 0.0:
#         return 0
#     cos_theta = x / math.sqrt(x*x+y*y)
#     theta = math.acos(cos_theta) / math.pi * 180
#     theta = theta if y > 0 else 360 - theta
#     if theta <= c_angle or theta >= 360 - c_angle:
#         label = 4
#     elif c_angle < theta < 90 - c_angle:
#         label = 3
#     elif 90 - c_angle <= theta <= 90 + c_angle:
#         label = 2
#     elif 90 + c_angle < theta < 180 - c_angle:
#         label = 1
#     elif 180 - c_angle <= theta <= 180 + c_angle:
#         label = 8
#     elif 180 + c_angle < theta < 270 - c_angle:
#         label = 7
#     elif 270 - c_angle <= theta <= 270 + c_angle:
#         label = 6
#     elif 270 + c_angle < theta < 360 - c_angle:
#         label = 5
#     return label

def discard_pattern(pattern):
    if len(pattern) > 1:
        for dir1, dir2 in tools.pairwise(pattern):
            if abs(dir1 - dir2) == 4:
                return True
    return False

def pattern2label(patterns, grid, version=0):
    labels = []
    discard_idxs = []
    # local direction
    if version == 0:
        for pattern in patterns:
            t_vx, t_vy = 0, 0
            for c1, c2 in tools.pairwise(pattern):
                vx, vy = c2[0] - c1[0], c2[1] - c1[1]
                t_vx += vx
                t_vy += vy
            labels.append(decide_label(t_vx, t_vy))
        pattern_set = [0, 1, 2, 3, 4, 5, 6 ,7, 8]
    # grid sequence
    elif version == 1:
        new_patterns = []
        for pattern in patterns:
            temp = [grid.cell2index(cid) for cid in pattern]
            xs = [idx[0] for idx in temp]
            ys = [idx[1] for idx in temp]
            x0, y0 = min(xs), min(ys)
            cid0 = grid.index2cell(x0, y0)
            new_pattern = []
            for idx in temp:
                if len(new_pattern)==0 or new_pattern[-1]!=(idx[0]-x0, idx[1]-y0):
                    new_pattern.append((idx[0]-x0, idx[1]-y0))
            new_patterns.append(tuple(new_pattern))
        print ('Origin Labels:', len(new_patterns))
        pattern_set = list(set(new_patterns))
        print ('Merged labels:', len(pattern_set))
        labels = [pattern_set.index(pattern) for pattern in new_patterns]
    # direction change
    elif version == 2:
        new_patterns = []
        len_stat = []
        for idx, pattern in enumerate(patterns):
            new_pattern = []
            x0, x1, y0, y1 = tools.bounding_box(pattern)
            length = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
            len_stat.append(length)
            # stationary
            if length < 5.0:
                new_pattern.append(0)
            # moving
            else:
                for c1, c2 in tools.pairwise(pattern):
                    vx, vy = c2[0] - c1[0], c2[1] - c1[1]
                    local_dir = decide_label(vx, vy)
                    if local_dir == 0:
                        continue
                    if len(new_pattern) == 0 or new_pattern[-1]!=local_dir:
                        new_pattern.append(local_dir)
                if len(new_pattern) == 0:
                    new_pattern.append(0)
                if discard_pattern(new_pattern):
                    discard_idxs.append(idx)
                    continue
            # if len(new_pattern) > 2:
            #     new_pattern = new_pattern[:2]
            new_patterns.append(tuple(new_pattern))
        print ('Origin Labels:', len(new_patterns))
        pattern_set = list(set(new_patterns))
        print ('Merged labels:', len(pattern_set))
        labels = [pattern_set.index(pattern) for pattern in new_patterns]
    return labels, pattern_set, discard_idxs, len_stat

def cellids2feature(cellids, towers, discard_idxs, version=0):
    features = []
    for idx, cellid in enumerate(cellids):
        if idx in discard_idxs:
            continue
        if version == 0:
            features.append((list(chain.from_iterable(cellid))))
        elif version == 1:
            feature = []
            for cid in chain.from_iterable(cellid):
                try:
                    lat, lng = towers[cid]
                except:
                    lat, lng = 0, 0
                feature.append(lat)
                feature.append(lng)
            features.append(feature)
        elif version == 2:
            feature = []
            u_towers = [utm.from_latlon(lat, lng)[:2] for lat, lng in towers]
            for mr in cellid:
                x0, y0 = u_towers[mr[0]]
                feature.append(x0)
                feature.append(y0)
                for i in range(1, len(mr)):
                    if mr[i] == -1:
                        lat, lng = 0, 0
                    else:
                        lat, lng = u_towers[mr[i]]
                        lat, lng = lat - x0, lng - y0
                    feature.append(lat)
                    feature.append(lng)
            features.append(feature)
    return features