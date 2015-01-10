
class Frames(object):
    "Low-level frame data model - object keeps sniffed pkts metadata"

    def __init__(self, db):
        self.db = db
        # Raw data
        self.all_frames = self.db['all_frames']
        self.all_frames.ensure_index('stamp')

        self.current_frames = self.db['current_frames']
        self.current_frames.ensure_index('stamp_utc', expireAfterSeconds=2*60*60)
        self.current_frames.ensure_index('stamp')
        self.current_frames.ensure_index('mac')


    ##
    # Generic sniff metadata
    def add(self, frame):
        "Add frame to database"
        #self.all_frames.insert(metadata)
        try:
            self.current_frames.insert(frame)
            self.all_frames.insert(frame)
        except:
            print "Frame storage failed on:"
            print repr(frame)
            raise


    def get_all_frames(self, since=0):
        frames = self.all_frames.find({'stamp': {'$gt': since}})
        frames.sort('stamp', 1)
        return frames

    def get_current_frames(self, since=0):
        frames = self.current_frames.find({'stamp': {'$gt': since}})
        frames.sort('stamp_utc', 1)
        return list(frames)
