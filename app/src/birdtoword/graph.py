import UserDict
import os
import logging
import time
import simplejson
from google.appengine.api import memcache

_baseBucketPath = os.path.join(os.path.dirname(__file__),'data')

class LazyBuckets(object):

    def __init__(self):
        self.data = {}
        self.__keys = [int(fn.split('.')[-1])
                       for fn in os.listdir(_baseBucketPath)
                       if '.dat.json.' in fn]
        logging.info("have buckets for: "+str(self.__keys))

    def __filepath(self, size):
        return os.path.join(_baseBucketPath,'buckets.dat.json.%s' % size)


    def has_key(self, key):
        return key in self.__keys

    def __len__(self):
        return len(self.__keys)

    def __getitem__(self, size):
        if not self.data.has_key(size) and size in self.__keys:
            bucket = memcache.get('bucket-%i' % size)
            if bucket is None:
                logging.info("loading bucket %i from %s" % (size, self.__filepath(size)))
                t1 = time.time()
                bucket = simplejson.load(open(self.__filepath(size)))
                logging.info("finished loading bucket %i in %s seconds" % (size, time.time()-t1))
                logging.info("%i words loaded" % len(bucket))
                memcache.set('bucket-%i' % size, bucket)
            else:
                logging.info("loading bucket %i from memcache" % size)
            self.data[size] = bucket
        return self.data[size]

    def get(self, key, default=None):
        if not self.has_key(key):
            return default
        return self[key]

BUCKETS = LazyBuckets()
