'''Caching code for all CMS DB Web services.

  * Each service has its own independent caches.

  * The caches are local to the backend, i.e. they is not shared with the other
    backends in production.

  * The caches are persistent in disk.

    This allows to reboot a machine without having to rebuild all the caches
    again for all services.

    However, they are still caches and should be used as that, not as databases.
    Cached objects could be lost at any time (they are not backed up)
    and they are flushed after each deployment to prevent problems with changes
    in the format of the objects.

  * The cache does not serialize Python objects. Therefore, if a service needs
    to store any Python object other than a string, it needs to be serialized.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import redis
import service


class Cache(object):
    '''A class representing a cache.
    '''

    def __init__(self, cacheID):
        self.cacheID = cacheID
        self.cache = redis.Redis(db = cacheID)


    def getCacheID(self):
        '''Returns the cache ID.
        '''

        return self.cacheID


    def get(self, key):
        '''Returns the value of the given key.
        '''

        return self.cache.get(key)


    def put(self, key, value, seconds = None):
        '''Sets the value for the given key.

        Optionally, specify an expiration time. Otherwise,
        the key is, by default, persistent.
        '''

        self.cache.set(key, value)

        if seconds is not None:
            self.expire(key, seconds)


    def delete(self, key):
        '''Deletes a key.
        '''

        self.cache.delete(key)


    def expire(self, key, seconds = None):
        '''Sets the expiration time for the given key.

        If seconds is None, makes the key persistent.
        '''

        if seconds is None:
            self.cache.persist(key)
        else:
            self.cache.expire(key, seconds)


    def ttl(self, key):
        '''Returns the seconds left until the key will expire,
        or None if the key is persistent (or does not exist).
        '''

        ttl = self.cache.ttl(key)

        if ttl == -1:
            return None

        return ttl


    def cacheCall(self, key, seconds):
        '''Decorator that caches a function call in a key for some seconds.

        This is one of the most common usage patterns for a cache.

        Note: it does not cache separate results for different arguments.
        '''

        def decorator(function):

            def newFunction(*args, **kwargs):
                data = self.get(key)
                if data is not None:
                    return data

                data = function(*args, **kwargs)
                self.put(key, data, seconds)
                return data

            return newFunction

        return decorator


# Instance the caches of the service
for (cache, cacheID) in service.settings['caches'].items():
    globals()[cache] = Cache(cacheID)

