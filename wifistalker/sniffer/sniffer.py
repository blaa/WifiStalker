import os
import sys
from time import time
from IPython import embed

from scapy import config, sendrecv

from wifistalker.model import db
from wifistalker import Log, WatchDog

from hopper import Hopper
from parser import PacketParser


class Sniffer(object):
    "Channel hopping, packet sniffing, parsing and finally storing"

    def __init__(self, interface, related_interface, sniffer_name, enable_hopping):
        self.sniffer_name = sniffer_name
        self.interface = interface
        self.enable_hopping = enable_hopping

        # Check interface existance
        if not self._iface_exists(interface):
            print "Exiting: Interface %s doesn't exist" % interface
            sys.exit(1)

        if related_interface and not self._iface_exists(related_interface):
            print "Exiting: Related interface %s doesn't exist" % interface
            sys.exit(1)

        # Logging
        header = 'SNIFF'
        if sniffer_name:
            header += '_' + sniffer_name
        self.log = Log(db, use_stdout=True, header=header)

        # Submodules
        self.packet_parser = PacketParser(self.log)
        self.hopper = Hopper(self.log, interface, related_interface)
        self.hopper.config(use_24=True, use_pop5=False)

        config.conf.sniff_promisc = 0
        self.log.info("Promiscuous mode disabled")

        self.watchdog = WatchDog()


    def _iface_exists(self, iface_name):
        "Check if interface exists"
        path = '/sys/class/net'
        iface_path = os.path.join(path, iface_name)
        try:
            _ = os.stat(iface_path)
            return True
        except OSError:
            return False

    def run(self):
        "Sniffer main loop"

        begin = time()
        pkts_all = 0

        sniff_begin = time()
        while True:
            start = time()

            # This catches KeyboardInterrupt,
            # TODO: Disable this catching + Probably hop on another thread and use prn argument.
            # But then - you'd have watchdog problems.
            pkts = sendrecv.sniff(iface=self.interface, count=10, timeout=0.1)
            pkts_all += len(pkts)
            for pkt in pkts:
                data = self.packet_parser.parse(pkt)
                if data is None:
                    continue

                data['ch'] = self.hopper.channel_number
                if ('PROBE_REQ' in data['tags'] or
                    'PROBE_RESP' in data['tags'] or
                    'ASSOC_REQ' in data['tags'] or
                    'DISASS' in data['tags']):
                    # Increase karma when client traffic is detected
                    self.hopper.increase_karma()

                db.add_packet_metadata(data, sniffer_name=self.sniffer_name)
            took = time() - start

            if self.enable_hopping:
                self.hopper.karmic_hop()

            if pkts_all % 10 == 0:
                took = time() - sniff_begin
                print "%d packets in %.2f min. (%.2f pps)" % (
                    pkts_all, took / 60.0,
                    pkts_all / took
                )

            self.watchdog.dontkillmeplease()
