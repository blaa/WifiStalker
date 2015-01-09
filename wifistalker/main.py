import sys
import os

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

    p.add_argument("-n", "--sniffer-name", dest="sniffer_name",
                   action="store", type=int,
                   help="sniffer name/tag")

    p.add_argument("--no-hop", dest="enable_hopping",
                   action="store_false", default=True,
                   help="Disable channel hopping")


    args = p.parse_args()
    return p, args


def action_sniff(args):
    "Run sniffing thread"
    from sniffer import Sniffer

    sniffer = Sniffer(args.interface,
                      args.related_interface,
                      sniffer_name=args.sniffer_name,
                      enable_hopping=args.enable_hopping)
    sniffer.run()

def action_analyze(args):
    "Run Analyzing thread"
    from analyzer import Analyzer
    analyzer = Analyzer()
    analyzer.run()

def action_webapp(args):
    "Run webapp thread"
    import webapp
    # Start webapp
    webapp.app.run()


def action_geo_load(args):
    "Import GEO data"
    import geoloc
    geoloc.run(args.geo_load)


def run():
    "Run WifiStalker"
    parser, args = _parse_arguments()
    if args.sniff:
        action_sniff(args)
    elif args.analyze:
        action_analyze(args)
    elif args.webapp:
        action_webapp(args)
    elif args.webapp:
        action_webapp(args)
    elif args.geo_load:
        action_geo_load(args)
    else:
        parser.print_help()
