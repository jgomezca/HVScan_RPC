import logging
import os
import hashlib
from datetime import datetime, timedelta
import pickle
import GTServerSettings as Settings

logger = logging.getLogger(__name__)


def cache_get(key, max_age=3600): #todo log errors
    logger.info("Trying to get key from cache. Key: " + str(key))
    try:
        filename = os.path.join(Settings.CACHE_DIR, hashlib.md5(key).hexdigest()+'.pkl')
        stat = os.stat(filename)
        fileage = datetime.fromtimestamp(stat.st_mtime)
        now = datetime.now()
        delta = now - fileage
        print delta,
        print timedelta(seconds=max_age)
        #print delta - datetime.timedelta(seconds=max_age)
        #return ['1']
        if delta > timedelta(seconds=max_age):
#            os.unlink(filename)
            pass
        else:
            with open(filename, 'rb') as f:
                 return pickle.load(f)
    except Exception as e:
        print e
        return None

def cache_put(key, value): #TODO log errors
    try:
        filename = os.path.join(Settings.CACHE_DIR, hashlib.md5(key).hexdigest()+'.pkl')
        with open(filename, 'wb') as f:
            pickle.dump(value, f)
    except Exception as e:
        print e
        pass

def cache_clean():
    pass
