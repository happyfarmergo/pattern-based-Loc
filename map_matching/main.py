import HMMM.preprocessing.osm_matcher as omr
import sys
import HMMM.mm_logger as mlogger
import logging

def main(argv):
    # mlogger.init_logger('map-matching', logging.DEBUG)
    mlogger.init_logger('map-matching', logging.INFO)
    omr.main(argv)
    return 0
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))