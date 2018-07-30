# -*- coding:utf-8 -*-
import tools

const_prefix = (
    "<!DOCTYPE html>\n"
    "<html>\n"
    "<head>\n"
    "<title>Simple Map</title>\n"
    "<meta name=\"viewport\" content=\"initial-scale=1.0\">\n"
    "<meta charset=\"utf-8\">\n"
    "<style>\n"
    "#map {\n"
    "height: 100%%;\n"
    "}\n"
    "html, body {\n"
    "height: 100%%;\n"
    "margin: 0;\n"
    "padding: 0;\n"
    "}\n"
    "</style>\n"
    "<link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.3.1/dist/leaflet.css\" integrity=\"sha512-Rksm5RenBEKSKFjgI3a41vrjkw4EVPlJ3+OiI65vTjIdo9brlAacEuKOiQ5OFh7cOI1bkDwLqdLw3Zg0cRJAAQ==\" crossorigin=\"\"/>\n"
    "<script src=\"https://unpkg.com/leaflet@1.3.1/dist/leaflet.js\" integrity=\"sha512-/Nsx9X4HebavoBvEBuyp3I7od5tA0UzAxs+j83KgC8PU0kgB4XiK4Lfe4y4cgBtaRJQEIFCW+oC506aPT2L1zw==\" crossorigin=\"\"></script>\n"
    "</head>\n"
    "<body>\n"
    "<div id=\"map\"></div>\n"
    "<script>\n"
    "var map = L.map('map').setView([%s, %s], 18);\n"
    "L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {\n"
    "maxZoom: 20,\n"
    "attribution: 'Map data &copy; <a href=\"http://openstreetmap.org\">OpenStreetMap</a> contributors, ' +\n"
            "'<a href=\"http://creativecommons.org/licenses/by-sa/2.0/\">CC-BY-SA</a>, ' +\n"
            "'Imagery © <a href=\"http://mapbox.com\">Mapbox</a>',\n"
        "id: 'mapbox.streets'\n"
    "}).addTo(map);\n\n"
)

const_suffix = (
    "</script>\n"
    "</body>\n"
    "</html>\n"
)

const_path = (
    "L.polyline(%s, {\n"
    "color: '%s',\n"
    "weight: 2,\n"
    "opacity: 0.6,\n"
    "}).addTo(map);\n"
)

const_path_pop = (
    "L.polyline(%s, {\n"
    "color: '%s',\n"
    "weight: 2,\n"
    "opacity: 0.6,\n"
    "}).addTo(map).bindTooltip('%s',{permanent:true, interactive:true}).openTooltip();\n"
)

const_marker = (
    "L.marker(%s).addTo(map);\n"
)

const_circle = (
    "L.circle(%s, {\n"
    "color: '%s',\n"
    "radius: %d,\n"
    "}).addTo(map);\n"
)

const_circle_pop = (
    "L.circle(%s, {\n"
    "color: '%s',\n"
    "radius: %d,\n"
    "}).addTo(map).bindTooltip('%s',{permanent:true, interactive:true}).openTooltip();\n"
)

const_marker_pop = "L.marker(%s).addTo(map).bindTooltip('%s',{permanent:true, interactive:true}).openTooltip();\n"

const_coor = (
    "var coor_%d = %s;\n"
)

colors = [
    '#000000',  # 黑色
    '#FF0000',  # 红色
    '#00FF00',  # 绿色
    '#FFFF00',  # 黄色
    '#0000FF',  # 蓝色
]

def df_to_html(df, out_fname, columns, more_info=False):
    lat_label, lng_label = columns
    c_lng, c_lat = df.iloc[0][lng_label], df.iloc[0][lat_label]
    html = const_prefix % (c_lat, c_lng)
    for i in range(len(df)):
        lng, lat = df.iloc[i][lng_label], df.iloc[i][lat_label]
        marker = '[%s, %s]' % (lat, lng)
        if more_info:
            html += const_circle_pop % (marker, 'red', 2, i)
        else:
            html += const_circle % (marker, 'red', 2)
    html += const_suffix
    with open(out_fname, 'w', encoding='UTF-8') as o_file:
        o_file.write(html)

def map_to_html(roadmap, out_fname):
    c_lat, c_lng = roadmap[list(roadmap.keys())[0]][0]
    html = const_prefix % (c_lat, c_lng)
    rid = 0
    for e_id, points in roadmap.items():
        p_str = []
        coors = '['
        for idx, point in enumerate(points):
            lat, lng = float(point[0]), float(point[1])
            marker = '[%s, %s]' % (lat, lng)
            p_str.append(marker)
        coors += ', '.join(p_str) + ']'
        html += const_coor % (rid, coors)
        html += const_path_pop % ('coor_' + str(rid), colors[rid % len(colors)], 'rid=' + str(e_id))
        rid += 1
    html += const_suffix
    with open(out_fname, 'w', encoding='UTF-8') as o_file:
        o_file.write(html)
