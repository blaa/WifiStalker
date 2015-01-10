import sys
import os
import config

from wifistalker import model

# Install faulthandler if it's available.
try:
    import faulthandler
    import signal
    faulthandler.enable()
    faulthandler.register(signal.SIGUSR1)
except ImportError:
    pass


def _parse_arguments():
    "Parse command line arguments"
    import argparse

    p = argparse.ArgumentParser(description='wifistalker')
    act = p.add_argument_group('actions')

    # Actions - mutually exclusive
    act.add_argument("-s", "--sniff", dest="sniff",
                     action="store_true",
                     help="run sniffing thread")

    act.add_argument("-a", "--analyze", dest="analyze",
                     action="store_true",
                     help="run analyzer thread")

    act.add_argument("-w", "--webapp", dest="webapp",
                     action="store_true",
                     help="run webapp thread")


    act.add_argument("--load-geo", dest="geo_load",
                     action="store", type=str, metavar="CSV_PATH",
                     help="load geolocational file")

    p.add_argument("-i", "--interface", dest="interface",
                   action="store", type=str, default="mon0",
                   help="interface")

    p.add_argument("-r", "--rel-interface", dest="related_interface",
                   action="store", type=str, default=None,
                   help="related interface to shutdown before sniffing")

    p.add_argument("--skip-2.4GHz", dest="use_24",
                   action="store_false", default=True,
                   help="don't hop over 2.4GHz channels")

    p.add_argument("--5GHz", dest="use_pop5",
                   action="store_true", default=False,
                   help="Add popular 5GHz channels")

    p.add_argument("-n", "--sniffer-name", dest="sniffer_name",
                   action="store", type=int,
                   help="sniffer name/tag")

    p.add_argument("--no-hop", dest="enable_hopping",
                   action="store_false", default=True,
                   help="Disable channel hopping")

    p.add_argument("--db-conn", dest="db_conn",
                   action="store", metavar="CONNSTR",
                   default=config.db['conn'], type=str,
                   help="Ex. mongodb://[username:password@]host1[:port1]/dbname")

    p.add_argument("--db-name", dest="db_name",
                   action="store", metavar="DBNAME",
                   default=config.db['name'], type=str,
                   help=u"Database name")


    args = p.parse_args()
    print "PARSED"
    return p, args


def action_sniff(db, args):
    "Run sniffing thread"
    from sniffer import Sniffer

    sniffer = Sniffer(db,
                      args.interface,
                      args.related_interface,
                      sniffer_name=args.sniffer_name,
                      enable_hopping=args.enable_hopping,
                      use_24=args.use_24,
                      use_pop5=args.use_pop5)
    sniffer.run()

def action_analyze(db, args):
    "Run Analyzing thread"
    from analyzer import Analyzer
    analyzer = Analyzer()
    analyzer.run()

def action_webapp(db, args):
    "Run webapp thread"
    import webapp
    # Start webapp
    webapp.app.run()

def action_geo_load(db, args):
    "Import GEO data"
    import geoloc
    geoloc.run(args.geo_load)

def init_db(args):
    "Open DB connection"
    db = model.DB(db_conn=args.db_conn, db_name=args.db_name)
    return db

def run():
    "Run WifiStalker"
    parser, args = _parse_arguments()

    db = init_db(args)

    if args.sniff:
        action_sniff(db, args)
    elif args.analyze:
        action_analyze(db, args)
    elif args.webapp:
        action_webapp(db, args)
    elif args.webapp:
        action_webapp(db, args)
    elif args.geo_load:
        action_geo_load(db, args)
    else:
        parser.print_help()
