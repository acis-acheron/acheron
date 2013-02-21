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
import config

log = logging.getLogger('acheron')

class Acheron(Daemon):
    def __init__(self, *args, **kwargs):
        Daemon.__init__(self, *args, **kwargs)
        self.styx_id = 0

    @staticmethod
    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
               )[20:24])

    @staticmethod
    def format_for_styx(msg):
        msg = json.dumps(msg)
        if config.styx_message_length > 0:
            padding = ' ' * (config.styx_message_length-1-len(msg)) + '\0'
        else:
            padding = ''
        return msg + padding

    def styx_call(self, method, *args):
        msg = self.format_for_styx({
            'jsonrpc': '2.0',
            'method': method,
            'params': [json.dumps(a) for a in args],
            'id': self.styx_id,
        })
        self.styx_socket.sendall(msg)
        self.styx_id += 1
        log.info('sent message to Styx: %s' % msg)

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

        try:
            self.styx_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except:
            log.critical('error creating Styx socket')
            sys.exit(1)

        try:
            self.styx_socket.connect(config.styx_unix_socket_path)
        except:
            log.critical('error connecting to Styx socket. %s does not exist' %
                         config.styx_unix_socket_path)
            sys.exit(1)

        while True:
            # alternatively, push to queue, peek, pop when confirmation received
            addr = self.ipop_listener.recv(16).strip()

            self.styx_call('addConfig',
                           [self.ipop_addr,
                            addr,
                            'keyexchange=ikev2'])
            result = self.styx_socket.recv(4096)
            log.info('received message from Styx: %s' % result)
            # acknowledge reply
