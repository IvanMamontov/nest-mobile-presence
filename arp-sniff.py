#! /usr/bin/env python3
import logging
import json
import os

from scapy.layers.l2 import ARP, sniff

known_devices = {}
master_devices = {}

logger = logging.getLogger()


def configure_logger():
    logging.basicConfig(level=logging.INFO)
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    fileHandler = logging.FileHandler("{0}.log".format('access'))
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)


def arp_monitor_callback(pkt):
    if ARP in pkt and pkt[ARP].op == ARP.who_has:
        mac_address = pkt[ARP].hwsrc
        if mac_address not in known_devices.keys():
            return pkt.sprintf("%ARP.hwsrc% %ARP.psrc% %ARP.op% {}".format(known_devices.get(mac_address, "Unknown")))
        elif mac_address in master_devices.keys():
            logger.info("Master device was detected {}".format(master_devices.get(mac_address)))
            # return pkt.sprintf("Master device was detected {}".format(master_devices.get(mac_address)))


if __name__ == "__main__":
    configure_logger()
    with open(os.path.join('conf', 'known-devices.json'), 'r') as conf:
        data = conf.read()
        known_devices = json.loads(data)

    with open(os.path.join('conf', 'master-devices.json'), 'r') as conf:
        data = conf.read()
        master_devices = json.loads(data)

    sniff(prn=arp_monitor_callback, filter="arp", store=0)
