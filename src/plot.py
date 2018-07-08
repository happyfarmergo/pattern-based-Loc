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

colors = [
    '#FF0000',  # 红色
    '#00FF00',  # 绿色
    '#E066FF',  # 黄色
    '#0000FF',  # 蓝色
]

def draw_pattern(grids, side, ca, axis, color, debug=False):
    for idx, bounding in enumerate(grids):
        x0, y0, x1, y1 = bounding
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        rec = Rectangle((x0, y0), width=side, height=side, ec=color, fill=False)
        if debug:
            ca.text(mx, my, str(idx), color='k', fontsize=10)
        ca.add_patch(rec)

