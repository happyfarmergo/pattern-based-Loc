import logging 
APP_NAME = 'map-matching'

def init_logger(app_name, level):
    logger = logging.getLogger(app_name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(app_name+'.log')
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.debug('logger start up...')