# -!- coding: utf-8 -*-

# Author: Tomasz bla Fortuna
# License: GPLv2

from pprint import pprint
from time import time, sleep
from collections import defaultdict

from wifistalker.model import Sender, SenderCache
from wifistalker import Log, WatchDog

class Analyzer(object):
    "Handle displaying"
    def __init__(self, db):
        self.db = db

        # Cache modified senders
        self.sender_cache = SenderCache(db)

        # Logging
        self.log = Log(self.db, use_stdout=True, header='ANALYZE')

        # Keeps me running if started correctly (bash loop, or device
        # reboot loop - for embedded)
        self.watchdog = WatchDog(interval=20)

        self.stats = {
            'already_analyzed': 0,
            'analyzed': 0,
        }

    def _analyze_frame(self, sender, frame):
        "Analyze a single frame and update sender object accordingly"

        tags = set(frame['tags'])

        #print "ADDING FRAME", frame, "TO", sender

        aggregate = sender.aggregate # Alias
        stat = sender.stat # Alias

        if aggregate['last_seen'] >= frame['stamp']:
            # We already updated sender using this frame
            self.stats['already_analyzed'] += 1
            return

        aggregate['last_seen'] = frame['stamp']
        if aggregate['first_seen'] == 0:
            aggregate['first_seen'] = frame['stamp']

        # Handle Tags
        if tags:
            x = set(aggregate['tags'])
            x.update(tags)
            aggregate['tags'] = list(x)

        if 'ASSOC_REQ' in tags:
            stat['assoc_req'] += 1

            if (frame['dst']
                and frame['dst'] != 'ff:ff:ff:ff:ff:ff'
                and frame['dst'] not in aggregate['assocs']):
                # Add association:
                aggregate['assocs'].append(frame['dst'])

        elif 'ASSOC_RESP' in tags:
            stat['assoc_resp'] += 1
        elif 'PROBE_REQ' in tags:
            stat['probe_req'] += 1
        elif 'PROBE_RESP' in tags:
            stat['probe_resp'] += 1
        elif 'DISASS' in tags:
            stat['disass'] += 1
        elif 'BEACON' in tags:
            sender.meta['station'] = True
            stat['beacons'] += 1

        stat['all'] += 1

        # Handle SSIDs and destinations
        ssid = frame['ssid']
        if ssid:
            if 'BEACON' in tags:
                aggregate['ssid_beacon'].append(ssid)
            elif 'PROBE_REQ' in tags:
                aggregate['ssid_probe'].append(ssid)
            else:
                # Not Beacon, not probe, something else.
                if sender.meta['station']:
                    # This is rather a beacon...
                    aggregate['ssid_beacon'].append(ssid)
                else:
                    # Or not?
                    aggregate['ssid_other'].append(ssid)


        if (frame['dst']
            and frame['dst'] != 'ff:ff:ff:ff:ff:ff'
            and frame['dst'] not in aggregate['dsts']):
            # Add destination:
            aggregate['dsts'].append(frame['dst'])

        """
        seen = {
            'stamp': frame['stamp'],
            'dst': frame['dst'],
            'freq': frame['freq'], # TODO: Remove?
            'str': frame['strength'],
            'tags': frame['tags']
        }
        """
        self.stats['analyzed'] += 1
        #sender.update_events(seen)

    def _analysis_loop(self, current, since):
        "Analyze until all senders got updated"
        only_src_macs = [] # Any at start
        last_stamp = None
        while True:
            iterator = self.db.frames.iterframes(current=current,
                                                 since=since,
                                                 src=only_src_macs)
            # Go throught the iterator
            for i, frame in enumerate(iterator):
                src = frame['src']
                sender = self.sender_cache.get(src)
                if sender is None:
                    sender = self.sender_cache.create(src)
                self._analyze_frame(sender, frame)
                last_stamp = frame['stamp']
                if (i+1) % 10000 == 0:
                    print "Done {0} frames, last stamp is {1}; {2}".format(i, last_stamp, self.stats)
                    self.watchdog.dontkillmeplease()

            if last_stamp is None:
                # No frames whatsoever
                return None

            # Try to save
            only_src_macs = self.sender_cache.store()

            if not only_src_macs:
                # Everything saved succesfully
                return last_stamp

            # Not everything saved, continue until everything is
            # written.
            self.log.info('Optimistic locking failed, analysis retry for %r', only_src_macs)


    def run_full(self):
        "Full data drop + reanalysis"

        # TODO - Drop in soft mode
        print 'Dropping existing knowledge in...'
        for i in range(3, 0, -1):
            print i, "second/s"
            sleep(1)
        self.db.knowledge.sender_drop()

        # Once
        self._analysis_loop(current=False, since=0)


    def run_continuous(self):
        "Continuous analysis"
        self.log.info('Starting continuous analysis')

        # One-time update for all knowledge entries
        #self._one_time_update()

        # Moving point-of-time from which we read frames
        since = 0
        while True:
            self.watchdog.dontkillmeplease()

            # Read current frames
            new_since = self._analysis_loop(current=True, since=since)
            if new_since is None:
                self.log.info('Waiting for frames')

                sleep(1)
                continue

            since = new_since




















    def _update_geo(self, senders):
        raise Exception()

        for sender in senders.itervalues():
            positions = self.db.geo.locate(mac=sender['mac'])
            for position in positions:
                sender.add_position(lat, lon)


    def _get_updated_senders(self, frames, ignore_macs=set()):
        "Update senders with frames - don't save them"

        raise Exception()

        updated_senders = {}
        new = 0
        frames_cnt = 0
        for frame in frames:
            mac = frame['src']
            frames_cnt += 1
            if mac in ignore_macs:
                continue

            if mac in updated_senders:
                # Get from cache
                sender = updated_senders[mac]
            else:
                # Get from DB
                sender = db.get_sender(mac)
                # Create new
                if sender is None:
                    print "NEW FOR", mac
                    sender = Sender()
                    sender.new(mac)
                    new += 1
                else:
                    sender['version'] += 1

            updated_senders[mac] = sender
            self._update_using_frame(sender, frame)
        msg = 'Knowledge <- %d frames, %d senders, %d new (%d ignored)' % (
            frames_cnt, len(updated_senders), new, len(ignore_macs)
        )
        print msg
        return updated_senders

    def _one_time_update(self):
        raise Exception()

        senders = db.get_knowledge()
        self._update_geo(senders)
        for mac, sender in senders.iteritems():
            # TODO: Don't update if nothing changed
            sender['version'] += 1
            ret = db.set_sender(sender)
        print "One time update finished", len(senders)

    def update_knowledge(self, frames):
        raise Exception()
        macs_updated = set()
        opti_failed = 1
        while opti_failed != 0:
            # Get senders and update them
            updated = self._get_updated_senders(frames,
                                                ignore_macs=macs_updated)
            self._update_geo(updated)

            # Try to store senders - handle optimistic locking
            opti_failed = 0
            for mac, sender in updated.iteritems():
                sender.short_seeings()
                ret = db.set_sender(sender)
                if ret == True:
                    macs_updated.add(mac)
                else:
                    msg = "Optimistic lock failed on %s" % mac
                    opti_failed += 1
                    self.log.info(msg)
                    print msg
