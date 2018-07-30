# -*- coding:utf-8 -*-
import sys
import utm
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.patches import Circle
from matplotlib.patches import Arrow
from matplotlib import lines
from collections import defaultdict

import tools

dir_dict = {0:(0.1, 0.1), 1:(-1, 1), 2:(0, 1), 3:(1, 1), 4:(1, 0), 5:(1, -1), 6:(0, -1), 7:(-1, -1), 8:(-1, 0)}

colors = [
    '#FF0000',  # 红色
    '#00FF00',  # 绿色
    '#0000FF',  # 蓝色
    '#E066FF',  # 黄色
]

def draw_pattern(label, ca, axis, color, debug=False):
    x0, x1, y0, y1 = axis
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            rec = Rectangle((x, y), width=1, height=1, ec=color, fill=False)
            ca.add_patch(rec)

    last_coor = (0, 0)
    for idx, local_dir in enumerate(label):
        x, y = dir_dict[local_dir]
        arrow = Arrow(last_coor[0], last_coor[1], x, y, color=colors[idx])
        ca.add_patch(arrow)
        last_coor = last_coor[0] + x, last_coor[1] + y

def draw_map(roadmap, ca, axis, debug=False):
    for rid, locs in roadmap.items():
        xs, ys = [], []
        for lat, lng in locs:
            x, y, _, _ = utm.from_latlon(lat, lng)
            xs.append(x)
            ys.append(y)
        line = lines.Line2D(xs, ys, linewidth=2, color=colors[rid%len(colors)])
        ca.add_line(line)

def draw_window_traj(coors, ca, axis, color, debug=False):
    for idx, (x, y) in enumerate(coors):
        circle = Circle((x, y), radius=10, color='y')
        ca.add_patch(circle)
        if debug:
            ca.text(x, y, str(idx), color=color, fontsize=18)
