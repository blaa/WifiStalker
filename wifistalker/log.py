from wifistalker.model import db

class Log(object):
    """Tiny mongodb/console logging

    TODO: Could be rewritten to use logging module with mongodb backend.
    """

    def __init__(self, db, use_stdout=False, header=None):
        self.db = db
        self.use_stdout = use_stdout
        self.header = header

    def _format(self, msg, level, *args, **kwargs):
        final = []
        if self.header:
            final.append(self.header)
            final.append('|' if level else ': ')

        if level:
            final.append(level + ": ")

        msg = msg.format(*args, **kwargs)
        final.append(msg)

        return "".join(final)

    def log(self, msg, level, *args, **kwargs):
        msg = self._format(msg, level, *args, **kwargs)

        if self.db:
            db.add_log(msg)

        if self.use_stdout:
            print msg

    def info(self, msg, *args, **kwargs):
        self.log(msg, '', *args, **kwargs)
