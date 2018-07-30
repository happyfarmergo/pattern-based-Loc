from multiprocessing import Pool
import os, time, random
import subprocess
import multiprocessing
import sys
from os import listdir
from os.path import isfile, join

def run_task(name, gap, dist, argv):
    print 'Run task %s (%s)...' % (name, os.getpid())
    start = time.time()
    max_tid, dataset, datatype = int(argv[0]), argv[1], argv[2]
    for tid in range(max_tid):
        string = "python main.py ../data/%s_map ../data/%s_%s/trajs/%d.txt %s %d %d %d" % (dataset, dataset, datatype, tid, name, dist, gap, (gap/60+1)*2000000)
        print string
        subprocess.call(string,shell=True)
        end = time.time()
        print 'Task %s_gap_%s_dist_%s runs %0.2f seconds.' % (name, str(gap), str(dist), (end - start))


if __name__=='__main__':

    gaps = [3]
    dists = [50]
    algs = ['HMM']
    for alg in algs:
        for gap in gaps:
            for dist in dists:
                run_task(alg, gap, dist, sys.argv[1:])
