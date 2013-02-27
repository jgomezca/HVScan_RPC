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


    def getCall(self, key, seconds, function, *args, **kwargs):
        '''Returns the key if available in the cache; if not, uses
        the function call to retrieve and return the value, saving it
        in the cache as well for next calls.

        This is one of the most common usage patterns for a cache.

        Consider using the cacheCall() decorator if you just want to cache
        all function calls, with automatic creation of different keys
        for different arguments. Use getCall() when you do not have
        a plain function (e.g. method call) or you need more control over
        the key naming.
        '''

        data = self.get(key)
        if data is not None:
            return data

        data = function(*args, **kwargs)
        self.put(key, data, seconds)
        return data


    def cacheCall(self, key = None, seconds = None, separator = '\0'):
        '''Decorator that caches a function call in a key for some seconds,
        creating different keys for different arguments, joining them
        as strings, e.g. a call to f(1, 2) with key 'myf' would be stored
        as key 'myf\01\02'.

        If key is None, only the arguments will be joined (this is different
        than being ''; the former allows to have f(1) stored as just "1").

        This is one of the most common usage patterns for a cache.

        The default separator is \0 since it is probably the safest in case
        the arguments are strings.

        Note: kwargs are *not* joined in the key name.
        '''

        def decorator(function):

            def newFunction(*args, **kwargs):
                argsList = list(args)
                if key is not None:
                    argsList = [key] + argsList
                return self.getCall(separator.join(map(str, argsList)), seconds, function, *args, **kwargs)

            return newFunction

        return decorator


# Instance the caches of the service
for (cache, cacheID) in service.settings['caches'].items():
    globals()[cache] = Cache(cacheID)

