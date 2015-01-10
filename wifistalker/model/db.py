import re
from time import time
import datetime

from frames import Frames
from knowledge import Knowledge
from map import Map

class DB(object):
    "Link to MongoDB + model factory"

    def __init__(self, db_conn, db_name):
        from pymongo import Connection

        print "Opening MongoDB connection"
        self.conn = Connection(host=db_conn)
        self.db = self.conn[db_name]

        # Open subcollections
        self.knowledge = Knowledge(self)
        self.frames = Frames(self)
        self.map = Map(self)

        # Log collection
        self._log = self['log']
        self._log.ensure_index('stamp_utc', expireAfterSeconds=60*60)


    def __getitem__(self, collection):
        "Create/get a collection"
        return self.db[collection]


    def log_add(self, s):
        obj = {
            'msg': s,
            'stamp_utc': datetime.datetime.utcnow(),
        }
        self._log.insert(obj)

    def log_get(self, count=10):
        logs = list(self._log.find().sort('stamp_utc', -1)[:count])
        return [x['msg'] for x in reversed(logs)]

