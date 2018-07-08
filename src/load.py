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
        rncid, cellid = piece_data['RNCID'], piece_data['CellID']
        lat, lng = piece_data['Latitude'], piece_data['Longitude']
        o_towers[(rncid, cellid)] = (i, lat, lng)
        t_towers.append((lat, lng))
    return o_towers, t_towers

def fill_utm_axis(df):
    xs, ys = [], []
    for i, piece_data in df.iterrows():
        x, y, _, _ = utm.from_latlon(piece_data['Latitude'], piece_data['Longitude'])
        xs.append(x)
        ys.append(y)
    df['UTM_X'] = xs
    df['UTM_Y'] = ys
    return df

def drop_dup_bytime(df):
    last_stp = 0
    dup_idxs = []
    df['MRTime'] = df['MRTime'].apply(lambda x: int(x) / 1000)
    for i, piece_data in df.iterrows():
        timestp = piece_data['MRTime']
        if last_stp == timestp:
            dup_idxs.append(i)
        last_stp = timestp
    df.drop(df.index[dup_idxs], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def load_data(data_file, gongcan_file):
    df = fill_utm_axis(pd.read_csv(data_file))
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
            else:
                out += 'keep[%d:%d]as id=%d\t' % (a, b, idx)
            idx += 1
        if debug:
            print(out)
    categories = []
    for idx, (a, b) in dbs.items():
        df_idx = df.loc[range(a,b)]
        df_idx['TrajID'] = idx
        categories.append(df_idx)
    return pd.concat(categories).reset_index(drop=True)