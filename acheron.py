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
from styx import StyxApi
from racoon import Racoon

import config

log = logging.getLogger('acheron')

class Acheron(Daemon):
    def __init__(self, *args, **kwargs):
        Daemon.__init__(self, *args, **kwargs)
        self.connections = set()

    @staticmethod
    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
               )[20:24])

    def __get_ipop_addr(self):
        sleep_count = 0
        while True:
            try:
                ipop_addr = self.get_ip_address('tapipop')
                log.info('found our IPOP IPv4 address: %s' % ipop_addr)
                return ipop_addr
            except IOError:
                if sleep_count % 10 == 0: # Keep from flooding our logs
                    log.critical('could not find IPOP IPv4 address. Sleeping.')
                time.sleep(0.5)
                sleep_count += 1

    def __get_api(self, name):
        log.info('using API: %s' % name)
        if name == 'styx':
            return StyxApi(
                config.styx_unix_socket_path,
            )
        if name == 'racoon':
            return Racoon(
                config.racoon_conf_path, self.ipop_addr, config.cert_path,
                config.priv_key_path
            )
        log.critial('unknown API: %s' % name)
        raise KeyError(name)

    def run(self):
        log.info('starting daemon')

        self.ipop_addr = self.__get_ipop_addr()
        self.api = self.__get_api(config.backend)

        try:
            self.ipop_listener = socket.socket(socket.AF_INET,
                                               socket.SOCK_DGRAM)
        except:
            log.critical('error creating IPOP socket')
            sys.exit(1)
        self.ipop_listener.bind((config.ipop_host, config.ipop_port))

        while True:
            addr = self.ipop_listener.recv(16).strip()
            log.info('received request for connection to %s' % addr)
            if addr in self.connections:
                log.info('discarding request for duplicate connection '
                         'to %s' % addr)
                continue
            self.connections.add(addr)
            self.api.add_peer(addr)
