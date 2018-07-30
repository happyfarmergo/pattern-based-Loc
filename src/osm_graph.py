from bs4 import BeautifulSoup as bs
import pandas as pd
from collections import defaultdict

jiading_ignore = [266205933, 266205935]
jiading_retain = [384531666, 384531667, 266221576, 263913992, 263913994, 135419990, 135372842, 135372843, 135372844, 135372845]
siping_ignore = []
siping_retain = []
extra_dict = {'jiading':(jiading_ignore, jiading_retain), 'siping':(siping_ignore, siping_retain)}

def load_nodes(inf_name, outf_name):
    data = bs(open(inf_name), 'xml')
    nodes = data.find_all('node')
    nodelist = []
    for node in nodes:
        nodelist.append([node['id'], node['lat'], node['lon']])
    df = pd.DataFrame(nodelist, columns=['old_id', 'lat', 'lon'])
    df['new_id'] = df.index
    df.to_csv(outf_name, index=False)

def load_ways(inf_name, outf_name, dataset):
    # retrive user specific ways
    data = bs(open(inf_name), 'xml')
    ways = data.find_all('way')
    way_kinds = ['motorway','motorway_link','primary','primary_link',\
            'secondary','secondary_link','tertiary', 'tertiary_link','residential','living_street',\
            'service','trunk','trunk_link','unclassified','road','track']
    highways = []
    need_ignore, need_retain = extra_dict[dataset]
    for w in ways:
        flag = False
        way_id = int(w.attrs['id'])
        for tag in w.find_all('tag'):
            if tag['k'] == 'highway':
                if tag['v'] in way_kinds and way_id not in need_ignore:
                    flag = True
                    break
                elif tag['v'] in ['pedestrian', 'footway'] and way_id in need_retain:
                    flag = True
                    break
        if flag:
            highways.append(w)
    # retrive oneways or twoways
    segMap = defaultdict(int)
    final_list = []
    for w in highways:
        way_id = int(w.attrs['id'])
        isOneway = False
        category = 'unclassified'
        for tag in w.find_all('tag'):
            if tag['k']=='oneway' and tag['v'] =='yes':
                isOneway = True
            if tag['k']=='highway':
                category = tag['v']
        ref_nodes = [nd['ref'] for nd in w.find_all('nd')]
        for ref_node in ref_nodes:
            segMap[ref_node] += 1

        if isOneway is False:
            final_list.append([way_id, False, category, ref_nodes])
            final_list.append([way_id, False, category, ref_nodes[::-1]])
        else:
            final_list.append([way_id, True, category, ref_nodes])
    # retrive road junctions
    junctions = set()
    for k in segMap.keys():
        if segMap[k] > 1:
            junctions.add(k)
    df = pd.DataFrame(final_list, columns=['id', 'oneway', 'category', 'nodes'])

    # retrive roads containing junctions
    for idx, row in df.iterrows():
        st = 0
        node_list = []
        for i in range(1, len(row['nodes'])-1):
            if row['nodes'][i] in junctions:
                node_list.append(row['nodes'][st:i+1])