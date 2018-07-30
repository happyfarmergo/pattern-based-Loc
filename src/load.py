# -*- coding:utf-8 -*-
import numpy as np
import pandas as pd
import utm
import math
import os
import sys
import bisect
import random
import tools
import matplotlib
import matplotlib.pyplot as plt
from collections import defaultdict

def get_config(data_set, data_type):
    max_dist = 100
    min_dist = 100
    min_len = 10
    max_again = 10
    if data_set == 'jiading' and data_type == '2g':
        pass
    elif data_set == 'jiading' and data_type == '4g':
        pass
    elif data_set == 'siping' and data_type == '2g':
        pass
    elif data_set == 'siping' and data_type == '4g':
        min_dist = 50
    return max_dist, min_dist, min_len, max_again

def bounding_box(df, a, b):
    coors = []
    for i in range(a, b):
        piece_data = df.loc[i]
        coors.append((piece_data['UTM_X'], piece_data['UTM_Y']))
    lats = [point[0] for point in coors]
    lngs = [point[1] for point in coors]
    x0, x1 = min(lats), max(lats)
    y0, y1 = min(lngs), max(lngs)
    return math.sqrt((x1-x0)**2 + (y1-y0)**2)

def trim_traj(df, a, b):
    delta = 0
    b = b - 1
    while df.loc[a]['Latitude'] == df.loc[a+1]['Latitude'] and df.loc[a]['Longitude'] == df.loc[a+1]['Longitude']:
        a += 1
        delta += 1
    while df.loc[b]['Latitude'] == df.loc[b-1]['Latitude'] and df.loc[b]['Longitude'] == df.loc[b-1]['Longitude']:
        b -= 1
        delta += 1
    assert a < b
    return a, b + 1, delta

def load_gongcan(gongcan_file):
    gongcan = pd.read_csv(gongcan_file)
    # merged cell tower, origin cell tower
    o_towers = dict()
    t_towers = []
    for i in range(len(gongcan)):
        piece_data = gongcan.iloc[i]
        rncid, cellid = int(piece_data['RNCID']), int(piece_data['CellID'])
        lat, lng = float(piece_data['Latitude']), float(piece_data['Longitude'])
        o_towers[(rncid, cellid)] = (i, lat, lng)
        t_towers.append((lat, lng)) 
    return o_towers, t_towers


def fill_utm_axis(df, source_col, target_col):
    xs, ys = [], []
    for i, piece_data in df.iterrows():
        x, y, _, _ = utm.from_latlon(piece_data[source_col[0]], piece_data[source_col[1]])
        xs.append(x)
        ys.append(y)
    df[target_col[0]] = xs
    df[target_col[1]] = ys
    return df

def drop_dup_bytime(df):
    last_stp = 0
    dup_idxs = []
    df['MRTime'] = df['MRTime'].apply(lambda x: int(x / 1000))
    for i, piece_data in df.iterrows():
        timestp = piece_data['MRTime']
        if last_stp == timestp:
            dup_idxs.append(i)
        last_stp = timestp
    df.drop(df.index[dup_idxs], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def load_data(data_file, gongcan_file):
    df = fill_utm_axis(pd.read_csv(data_file), ['Latitude', 'Longitude'], ['UTM_X', 'UTM_Y'])
    df = drop_dup_bytime(df)
    return df

def clean_data(df, max_dist, min_dist, min_len, max_again, debug=False):
    max_trid = max(df['TrajID'])
    dbs = dict()
    idx = 0
    for i in range(max_trid + 1):
        df_i_idx = df[df['TrajID']==i].index
        ranges = [df_i_idx[0]]
        out = 'Traj ID=%d\n' % i
        for p, q in tools.pairwise(df_i_idx):
            x1, y1 = df.loc[p]['UTM_X'], df.loc[p]['UTM_Y']
            x2, y2 = df.loc[q]['UTM_X'], df.loc[q]['UTM_Y']
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if dist > max_dist:
                out += '%d->%d:%sm\t' % (p, q, int(dist))
                ranges.append(q)
        ranges.append(df_i_idx[-1] + 1)
        out += '\n'
        remain = []
        for a, b in tools.pairwise(ranges):
            bounding = bounding_box(df, a, b)
            if b - a < min_len or bounding < min_dist:
                out += 'discard[%d:%d]=%dm\t' % (a, b-1, int(bounding))
                continue
            c, d, delta = trim_traj(df, a, b)
            dbs[idx] = (c, d) if delta > max_again else (a, b)
            if delta > max_again:
                out += 'trimed[%d,%d] ' % (c - a, b - d)
                out += 'keep[%d:%d]as id=%d\t' % (c, d-1, idx)
                remain.append(d-c)
            else:
                out += 'keep[%d:%d]as id=%d\t' % (a, b-1, idx)
                remain.append(b-a)
            idx += 1
        if debug:
            print(out)
            print(remain)
    categories = []
    for idx, (a, b) in dbs.items():
        df_idx = df.loc[range(a,b)]
        df_idx['TrajID'] = idx
        categories.append(df_idx)
    return pd.concat(categories).reset_index(drop=True)

def load_matching(output_folder, max_trid, dist):
    result = []
    for tr_id in range(max_trid + 1):
        filename = output_folder + '/' + str(tr_id) + '.txt.HMM.G_gap=3_dist=' + str(dist) + '.txt'
        with open(filename) as fin:
            for line in fin:
                data = line.strip().split(',')
                if len(data)!=8:
                    continue
                data = [float(x) for x in data]
                data[0] = int(data[0])
                data[3] = int(data[3])
                if data[4] == 0:
                    continue
                data.insert(0, tr_id)
                result.append(data)
    return pd.DataFrame(result, columns=['TrajID', 'MRTime', 'Latitude', 'Longitude', 'RoadID', 'Match_Lat', 'Match_Lng', 'Match_loc', 'Match_Dist'])

jiading_ignore = [266205933, 266205935]
jiading_retain = [384531666, 384531667, 266221576, 263913992, 263913994, 135419990, 135372842, 135372843, 135372844, 135372845]
siping_ignore = []
siping_retain = []
extra_dict = {'jiading':(jiading_ignore, jiading_retain), 'siping':(siping_ignore, siping_retain)}

def load_map(map_file, edge_file, node_file, dataset):
    roadmap, edgemap, nodemap = dict(), dict(), dict()
    need_ignore, need_retain = extra_dict[dataset]
    with open(map_file, encoding='UTF-8') as f:
        for line in f:
            nodes = []
            line_arr = line.strip().split('^')
            rid = int(line_arr[0])
            way_type = line_arr[2]
            # if way_type in ['pedestrian', 'footway', 'steps']:
            #     if rid not in need_retain:
            #         continue
            # else:
            #     if rid in need_ignore:
            #         continue
            data = [float(d) for d in line_arr[4:]]
            lngs, lats = data[1::2], data[::2]
            roadmap[rid] = [(lat, lng) for lat, lng in zip(lats, lngs)]
    with open(edge_file, encoding='UTF-8') as f:
        for line in f:
            data = line.strip().split(' ')
            rid, st, et = int(data[0]), int(data[1]), int(data[2])
            edgemap[rid] = [st, et]
    with open(node_file, encoding='UTF-8') as f:
        for line in f:
            data = line.strip().split(' ')
            nid, lat, lng = int(data[0]), float(data[1]), float(data[2])
            nodemap[nid] = (lat, lng)
    return roadmap, edgemap, nodemap

def restore_map(map_file, edge_file, restore_rids):
    restored = []
    with open(map_file, encoding='UTF-8') as f:
        for line in f:
            line_arr = line.strip().split('^')
            rid = int(line_arr[0])
            if rid in restore_rids:
                restored.append(line)
    print ('restored map_file:' + str(len(restored)))
    with open(map_file, 'w', encoding='UTF-8') as f:
        f.write(''.join(restored))
    restored = []
    with open(edge_file, encoding='UTF-8') as f:
        for line in f:
            line_arr = line.strip().split(' ')
            rid = int(line_arr[0])
            if rid in restore_rids:
                restored.append(line)
    print ('restored edge_file:' + str(len(restored)))
    with open(edge_file, 'w', encoding='UTF-8') as f:
        f.write(''.join(restored))


def to_trajs(df, out_folder):
    max_trid = max(df['TrajID'])
    for tr_id in range(max_trid + 1):
        s_traj = ''
        for i, row in df[df['TrajID']==tr_id].iterrows():
            s_traj += '%s,%s,%s\n' % (row['MRTime'], row['Latitude'], row['Longitude'])
        with open(out_folder + '/' + str(tr_id) + '.txt', 'w') as fout:
            fout.write(s_traj)
