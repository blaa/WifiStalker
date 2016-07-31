# Author: Tomasz bla Fortuna
# License: GPLv2

import re
from time import time

from sender import Sender

class Knowledge(object):
    """High-level data model - knowledge about Senders and their Presence.

    Stores, queries, updates Sender objects stored in MongoDB
    instance. Manages the knowledge about the Senders and Presence.
    """

    def __init__(self, db):
        self.db = db

        # Aggregated data about a specific MAC - a knowledge.
        self.knowledge = self.db['knowledge']

        self.knowledge.ensure_index('mac')
        self.knowledge.ensure_index('aggregate.last_seen')
        self.knowledge.ensure_index('aggregate.ssid_probe')
        self.knowledge.ensure_index('aggregate.ssid_beacon')

        # Resolving vendor names
        # TODO: Should be loaded once into Mongo and cached from there.
        self._load_vendors()

    ##
    # Vendors
    def _load_vendors(self):
        "Load vendors from OUI file"
        self.vendors = {}
        try:
            with open('oui.txt', 'r') as f:
                for line in f:
                    m = re.match(r'^  ([0-9A-Z]{6}) +\(base 16\)[ \t]+(.*)$', line)
                    if m is None:
                        continue
                    mac, vendor = m.groups()
                    self.vendors[mac] = vendor
                print "Registered", len(self.vendors), "vendors"
        except IOError:
            print "Unable to open oui.txt - program won't resolve MAC addresses into producers"
            self.vendors = {}

    def get_vendor(self, mac):
        "Determine vendor by MAC"
        vendor = mac.replace(':', '')[:6]
        return self.vendors.get(vendor.upper(), 'unknown').strip()

    ##
    # Sender knowledge
    def sender_query(self, mac=None, sort='last_seen', time_window=None,
                     ssid_filter=None, tag_filter=None, advanced=None, count=None):
        """Query the database for a sender by it's MAC address.

        If mac is None - return a list of all senders.
        sort can start with `-' to change sort direction

        time_window - recently seen (X seconds) senders only
        """
        # Parse sorting order
        direction = 1
        if sort.startswith('-'):
            direction = -1
            sort = sort[1:]

        # Build query
        where = {}

        if mac is not None:
            where['mac'] = mac.lower()

        if time_window:
            now = time()
            where['aggregate.last_seen'] = {
                '$gt': now - time_window
            }

        if ssid_filter:
            where['$or'] = [
                {'aggregate.ssid_probe': {'$in': ssid_filter}},
                {'aggregate.ssid_beacon': {'$in': ssid_filter}},
            ]
        if tag_filter:
            where['user.tags'] = {
                '$all': tag_filter
            }

        if advanced is not None:
            where.update(advanced)

        senders = self.knowledge.find(where).sort(sort, direction)
        if count is not None:
            senders = senders[:count]
        return Sender.create_from_db(senders)


    def alias_query(self, mac_list):
        "Given a list of MAC addresses return a mapping mac -> alias"
        where = {
            'mac': {
                '$in': [m.lower() for m in mac_list]
            }
        }
        result = self.knowledge.find(where, {'mac': 1, 'user.alias': 1})
        mapping = {}
        for entry in result:
            mapping[entry['mac']] = entry['user']['alias']
        return mapping


    def sender_store(self, sender):
        "Write sender back to the database while handling optimistic locking"
        if sender.version is None:
            # It's new, just insert as version 0.

            obj = sender.get_dict()
            obj['version'] = 0

            assert self.sender_query(mac=sender.mac) == [] # Remove this check later
            ret = self.knowledge.insert(obj)
            assert ret is not None
            # Mark version at this point in the object
            sender.version = 0
        else:
            obj = sender.get_dict()
            obj['version'] += 1
            ret = self.knowledge.update({'mac': obj['mac'],
                                        'version': obj['version'] - 1},
                                        obj,
                                        upsert=False)
            if ret['n'] != 1:
                print "Optimistic locking failed", ret
                return False
            else:
                # Correctly written
                sender.version = obj['version']
        return True

    def sender_drop(self, mac=None):
        "Remove sender(s) from knowledge - all if mac is None"
        if mac is not None:
            where = {'mac': mac}
        else:
            where = None
        ret = self.knowledge.remove(where)
        print "Dropped {ret[n]} knowledge entries".format(ret=ret)

    def cleanup(self):
        "Soft cleanup without removing user data (alias, name)"
        senders = self.sender_query()


    def sender_tag(self, srcs, tags, types=None, untag=False):
        u"Add tags to senders"
        where = {}
        if types not in [None, 'all']:
            if types == 'clients':
                where['meta.ap'] = False
            elif types == 'aps':
                where['meta.ap'] = True
            else:
                assert False, "Invalid `types' argument"

        where['mac'] = {'$in': srcs}

        if untag is False:
            operation = {
                '$addToSet': { 'user.tags': { '$each': tags } }
            }
        else:
            operation = {
                '$pullAll': { 'user.tags': tags }
            }

        # Increment version
        operation['$inc'] = {'version': 1}

        print operation

        ret = self.knowledge.update(where, operation, multi=True)
        return ret['n']
