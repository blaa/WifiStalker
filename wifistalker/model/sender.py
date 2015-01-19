# Author: Tomasz bla Fortuna
# License: GPLv2

class Sender(object):
    """Aggregated knowledge about a single Sender.

    Sender (Host) - a node identified by a specific MAC address for which we aggregate information.
    Information is in the whole called `knowledge'.
    """

    @classmethod
    def create_from_db(cls, results):
        u"Create list of Sender objects from DB results"
        senders = []
        for result in results:
            s = Sender(result['mac'], result)
            senders.append(s)
        return senders

    def __init__(self, mac, db_entry=None):
        if db_entry is not None:
            self._load_from_db(mac, db_entry)
        else:
            self.reset(mac, hard=True)

    def _load_from_db(self, mac, db_entry):
        "Load from DB entry"
        try:
            assert mac == db_entry['mac']
            self.mac = mac
            self.version = db_entry['version']

            self.user = db_entry['user']
            self.stat = db_entry['stat']
            self.meta = db_entry['meta']
            self.events = db_entry['events']
            self.aggregate = db_entry['aggregate']
        except KeyError:
            print "Invalid scheme version, available keys:"
            print db_entry.keys()
            print
            raise

    def get_dict(self):
        return {
            'mac': self.mac,
            'version': self.version,
            'user': self.user,
            'meta': self.meta,
            'stat': self.stat,
            'events': self.events,
            'aggregate': self.aggregate,
        }

    def reset(self, mac=None, hard=False):
        "Drop data and initialize object. Hard drops user data as well."

        # MAC Address
        if mac is not None:
            self.mac = mac

        # Optimistic locking
        if hard is True:
            self.version = None
        else:
            assert self.version >= 0

        if hard:
            self.user = {
                # Owner and alias if known.
                'owner': None,
                'notes': None,
                'alias': None,
            }
        else:
            assert hasattr(self, 'user')
            assert 'owner' in self.user

        self.stat = {
            # Pkts stats
            'beacons': 0,
            'assoc_req': 0,
            'assoc_resp': 0,
            'probe_req': 0,
            'probe_resp': 0,
            'disass': 0,
            'all': 0,
        }

        self.meta = {
            'station': False,
            'vendor': None,

            # Geographical positions
            'geo': [],

            # Recent average strength (running average)
            'running_str': -90.0,
        }

        # Seeings, not really straight-forward data. Heavy filtered packets
        # [{stamp_from, stamp_to, pkts, avg_strength}, ...]
        self.events = []

        # Aggregated data
        self.aggregate = {
            # First / last seen
            'last_seen': 0,
            'first_seen': 0,

            # All essids probed or beaconed
            'ssid_probe': [],
            'ssid_beacon': [],
            'ssid_other': [],

            # All association tries
            'assocs': [],

            # All found packet destinations
            'dsts': [],

            # Aggregated tags
            'tags': [],
        }

    def __repr__(self):
        name = self.mac if self.user['alias'] is None else self.user['alias']
        s = '<Sender %s pkts=%d station=%s>' % (
            name,
            self.stat['all'],
            self.meta['station']
        )
        return s

    def add_geo(self, location):
        """Add geographical tag to the sender

        Layout:
        { lat: 0.1, lon: 0.2, source: 'ow' }
        """
        if location in self.meta['geo']:
            return
        self.meta['geo'].append(location)

    def add_event(self, seen):
        # Filter the same and not interesting stuff
        if not self['seen']:
            self['seen'].append(seen)
            return

        self['running_str'] = ((self['running_str'] * 10.0) + seen['str']) / 11.0

        prev = self['seen'][-1]

        if seen['stamp'] - prev['stamp'] > 5: # over 5 seconds
            self['seen'].append(seen)
            return

        if (prev['tags'] == seen['tags']
            and prev['dst'] == seen['dst']
            and abs(prev['str'] - seen['str']) < 8):
            return

        self['seen'].append(seen)


class SenderCache(object):
    """App-level sender object cache.

    We don't operate on senders in the DB, but read them, change
    and save back. Saving might fail because of optimistic
    locking - which is handled by the Knowledge.
    """

    def __init__(self, db):
        self.db = db
        self.reset()

    def reset(self):
        "Reset cache"
        # Sender object cache
        self.cache = {}

    def get(self, mac):
        "Get sender from cache or from the DB - and then cache."
        # Cache
        if mac in self.cache:
            return self.cache[mac]

        # DB
        res = self.db.knowledge.sender_query(mac=mac)
        if not res:
            return None
        else:
            assert len(res) == 1
            sender = res[0]
            self.cache[mac] = sender
            return sender

    def iteritems(self, *args, **kwargs):
        return self.cache.iteritems(*args, **kwargs)

    def create(self, mac):
        "Create a new sender object"
        sender = Sender(mac)
        self.cache[mac] = sender
        return sender

    def store(self):
        "Store each element in the cache, returning a list of failed objects"
        correct = 0
        failed = []
        for mac in self.cache.keys():
            sender = self.cache[mac]
            ret = self.db.knowledge.sender_store(sender)
            if ret is False:
                failed.append(mac)
                # Invalidate entry
                self.cache.pop(mac)
            else:
                correct += 1
        if failed:
            print "Stored sender cache. correct={0} failed={1}".format(correct, len(failed))
        return failed

    def __repr__(self):
        return "<SenderCache entries={0}>".format(len(self.cache))
