#!/usr/bin/env python

from __future__ import print_function
import socket
import sys
import json
import logging
import fcntl
import struct
import array
import time

from daemon import Daemon
from styx import Styx
import config

log = logging.getLogger('acheron')

class Acheron(Daemon):
    def __init__(self, *args, **kwargs):
        Daemon.__init__(self, *args, **kwargs)
        self.styx = Styx(config.styx_unix_socket_path)

    @staticmethod
    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
               )[20:24])


    def run(self):
        log.info('starting daemon')
        try:
            self.ipop_addr = self.get_ip_address('tapipop')
        except IOError:
            log.critical('error finding our IPOP address. Sleeping.')
            time.sleep(1.0)
            self.run()
        
        try:
            self.ipop_listener = socket.socket(socket.AF_INET,
                                               socket.SOCK_DGRAM)
        except:
            log.critical('error creating IPOP socket')
            sys.exit(1)
        self.ipop_listener.bind((config.ipop_host, config.ipop_port))

        while True:
            # alternatively, push to queue, peek, pop when confirmation received
            addr = self.ipop_listener.recv(16).strip()

            self.styx.addConfig(
                self.ipop_addr,
                addr,
                'keyexchange=ikev2'
            )
