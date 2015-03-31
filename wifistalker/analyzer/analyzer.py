# -!- coding: utf-8 -*-

# Author: Tomasz bla Fortuna
# License: GPLv2

from pprint import pprint
from time import time, sleep
from collections import defaultdict

from wifistalker.model import Sender, SenderCache
from wifistalker import Log, WatchDog
from wifistalker import config

class Analyzer(object):
    """Handle packet analysis.

    TODO: Split into two classes - one doing analysis, second with generic analysis logic.
    """
    def __init__(self, db):
        self.db = db

        # Cache modified senders
        self.sender_cache = SenderCache(db)

        # Context - for tagging
        # sniffer name -> tag -> last seen timestamp
        self.tag_context = defaultdict(lambda: {})

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

        frame_tags = set(frame['tags'])

        aggregate = sender.aggregate # Alias
        stat = sender.stat # Alias
        stamp = frame['stamp'] # Alias

        if aggregate['last_seen'] >= stamp:
            # We already updated sender using this frame
            self.stats['already_analyzed'] += 1
            return

        aggregate['last_seen'] = stamp
        if aggregate['first_seen'] == 0:
            aggregate['first_seen'] = stamp

        # Handle frame tags
        if frame_tags:
            x = set(aggregate['tags'])
            x.update(frame_tags)
            aggregate['tags'] = list(x)

        # Update stats based on frame_tags
        if 'ASSOC_REQ' in frame_tags:
            stat['assoc_req'] += 1
        elif 'ASSOC_RESP' in frame_tags:
            stat['assoc_resp'] += 1
        elif 'PROBE_REQ' in frame_tags:
            stat['probe_req'] += 1
        elif 'PROBE_RESP' in frame_tags:
            stat['probe_resp'] += 1
        elif 'DISASS' in frame_tags:
            stat['disass'] += 1
        elif 'BEACON' in frame_tags:
            stat['beacons'] += 1
        elif 'DATA' in frame_tags:
            stat['data'] += 1
        elif 'IP' in frame_tags:
            stat['ip'] += 1

        stat['all'] += 1

        # Handle SSIDs and destinations
        ssid = frame['ssid']
        if ssid:
            if 'BEACON' in frame_tags:
                if ssid not in aggregate['ssid_beacon']:
                    aggregate['ssid_beacon'].append(ssid)
            elif 'PROBE_REQ' in frame_tags:
                if ssid not in aggregate['ssid_probe']:
                    aggregate['ssid_probe'].append(ssid)
            else:
                # Not Beacon, not probe, something else.
                pass
                #if ssid not in aggregate['ssid_other']:
                #    aggregate['ssid_other'].append(ssid)
                """
                if sender.meta['ap']:
                    # This is rather a beacon...
                    if ssid not in aggregate['ssid_beacon']:
                        aggregate['ssid_beacon'].append(ssid)
                else:
                    # Or not?
                    if ssid not in aggregate['ssid_other']:
                        aggregate['ssid_other'].append(ssid)
                """


        if frame['dst']:
            sender.add_dst(frame['dst'], frame_tags)

        if frame['strength']:
            sender.meta['running_str'] = (sender.meta['running_str'] * 10.0 + frame['strength']) / 11.0

        # Is it an AP or a client? By default - client, more points -
        # more likely to be a station.
        # Phone can send beacons. But APs can send probes too.
        pts = 0
        if stat['probe_resp'] > stat['probe_req']:
            pts += 1
        if (100.0 * stat['beacons'] / stat['all']) > 50:
            pts += 1
        if (100.0 * stat['beacons'] / stat['all']) > 80:
            pts += 1
        if stat['beacons'] < 10:
            pts -= 1
        pts += len(aggregate['ssid_beacon'])
        pts -= len(aggregate['ssid_probe'])

        if stat['probe_req'] > 0:
            pts += 1

        if pts >= 2:
            sender.meta['ap'] = True
        else:
            sender.meta['ap'] = False

        ##
        # Tag context update
        # tags - tags from current frame.
        sniffer = frame['sniffer']
        tag_virality = config.analyzer['tag_virality']

        if sender.meta['ap']:
            # Update +tags to context
            for tag in sender.user['tags']:
                if tag.startswith('+'):
                    self.tag_context[sniffer][tag] = stamp
        else:
            # Add tags currently in context into knowledge.
            for tag, tag_stamp in self.tag_context[sniffer].items():
                if tag_stamp + tag_virality < stamp:
                    del self.tag_context[sniffer][tag]
                    continue
                if tag in sender.user['tags']:
                    continue
                sender.user['tags'].add('-' + tag[1:])

        """
        seen = {
            'stamp': stamp,
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
        frames_total = 0

        # Repeat this iterator until all senders are correctly saved.
        cnt = 0
        while True:
            last_stamp = None
            iterator = self.db.frames.iterframes(current=current,
                                                 since=since,
                                                 src=only_src_macs,
                                                 limit=500000)
            # Go throught the iterator
            for cnt, frame in enumerate(iterator):
                src = frame['src']
                sender = self.sender_cache.get(src)
                if sender is None:
                    sender = self.sender_cache.create(src)
                self._analyze_frame(sender, frame)
                last_stamp = frame['stamp']
                if (cnt+1) % 20000 == 0:
                    now = time()

                    seconds = int(now - last_stamp)
                    hours = seconds / 60 / 60
                    print "Done {0} frames, senders={1} last is {2} hours ago;".format(cnt+1,
                                                                                       len(self.sender_cache),
                                                                                       hours)
                    self.watchdog.dontkillmeplease()
            s = "Analyzed {0} frames, last stamp is {1}; Analyzed total={2[analyzed]}"
            frames_total += cnt
            print s.format(cnt, last_stamp, self.stats)

            if last_stamp is None:
                # No frames whatsoever
                print 'Reached end of frames - exiting'
                return None

            # Update statics before storing
            for mac, sender in self.sender_cache.iter_dirty_items():
                self._update_static(sender)
                self.watchdog.dontkillmeplease()

            # Try to save
            only_src_macs = self.sender_cache.store(lambda: self.watchdog.dontkillmeplease())

            if not only_src_macs:
                # Everything saved succesfully
                return (last_stamp, frames_total)

            # Not everything saved, continue until everything is
            # written.
            self.log.info('Optimistic locking failed, analysis retry for %r', only_src_macs)

            # Continue `while True' loop until all are saved.


    def run_full(self):
        "Full data drop + reanalysis"

        print 'Dropping existing knowledge (leaving user data) in...'
        for i in range(3, 0, -1):
            print i, "second/s"
            sleep(1)

        print 'Soft dropping knowledge'
        senders = self.db.knowledge.sender_query()
        for sender in senders:
            sender.reset(hard=False)
            self.db.knowledge.sender_store(sender)
            self.watchdog.dontkillmeplease()

        # Once
        print 'Entering analyze loop'
        #since = time() - 60*60*3 # FIXME SHOULD BE ZERO, DEBUG
        since = 0
        while True:
            ret = self._analysis_loop(current=False, since=since)
            if ret is not None:
                since, frames_total = ret
            else:
                # End of work
                break


    def run_continuous(self):
        "Continuous analysis"
        self.log.info('Starting continuous analysis')

        # One-time update for all knowledge entries
        #self._one_time_update()

        # Reduce CPU usage by analyzing more frames in one go while
        # trying to keep this number low to get frequent updates for
        # the UI.
        interval = 3

        # `since' creates a moving point-of-time from which we read frames.
        # Initialize with timestamp of last analysis
        result = self.db.knowledge.sender_query(count=1, sort='-aggregate.last_seen')
        if result:
            since = result[0].aggregate['last_seen'] - 1
        else:
            since = 0

        print "Starting from ", time() - since, "seconds in the past"

        while True:
            self.watchdog.dontkillmeplease()

            # Read current frames
            ret = self._analysis_loop(current=True, since=since)

            # Try to analyze 150 - 250 frames in one pass
            new_since, frames_total = ret if ret else (since, 0)
            if frames_total < 150 and interval < 10:
                interval += 0.5
                print "interval is", interval
            if frames_total > 250 and interval > 1:
                interval -= 1 if interval > 1 else 0.1
                print "interval is", interval

            self.watchdog.dontkillmeplease()
            sleep(interval)
            since = new_since



    def _update_static(self, sender):
        # Decode vendor
        sender.meta['vendor'] = self.db.knowledge.get_vendor(sender.mac)

        # Decode GEO location based on bssid/mac
        locations = self.db.geo.locate(mac=sender.mac)
        for loc in locations:
            sender.add_geo(loc)


    def _one_time_update(self):
        raise Exception()

        senders = db.get_knowledge()
        self._update_geo(senders)
        for mac, sender in senders.iteritems():
            # TODO: Don't update if nothing changed
            sender['version'] += 1
            ret = db.set_sender(sender)
        print "One time update finished", len(senders)
