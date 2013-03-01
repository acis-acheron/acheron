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
        self.styx = Styx(config.styx_unix_socket_path)
        
        sleep_count = 0
        while True:
            try:
                self.ipop_addr = self.get_ip_address('tapipop')
                log.info('found IPOP IPv4 address: %s' % self.ipop_addr)
                break
            except IOError:
                if sleep_count % 10 == 0:
                    log.critical('could not find IPOP IPv4 address. Sleeping.')
                time.sleep(0.5)
                sleep_count += 1
        
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
            conn_id = self.styx.message_id

            self.styx.addConfig(
                'conn_%d' % conn_id,
                self.ipop_addr,
                addr,
                'leftcert=myCert.pem',
                'rightid=%any',
                'leftid=%any',
                'keyexchange=ikev2'
            )
            self.styx.connect(
                False,
                'conn_%d' % conn_id
            )
