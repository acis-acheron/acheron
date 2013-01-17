#!/usr/bin/env python

from __future__ import print_function
from daemon import Daemon
import socket
import sys
import json
import logging

log = logging.getLogger('acheron')

class Acheron(Daemon):
    def __init__(self, *args, **kwargs):
        Daemon.__init__(self, *args, **kwargs)
        self.styx_id = 0

    @staticmethod
    def format_for_styx(msg):
        msg = json.dumps(msg)
        return msg + ' '*(4095-len(msg)) + '\0'

    def styx_call(self, method, *args):
        self.styx_socket.sendall(self.format_for_styx({
            'jsonrpc': '2.0',
            'method': method,
            'params': [json.dumps(a) for a in args],
            'id': self.styx_id,
        }))
        self.styx_id += 1

    def run(self):
        log.info('Starting daemon')
        try:
            self.ipop_listener = socket.socket(socket.AF_INET,
                                               socket.SOCK_DGRAM)
        except:
            log.critical('error creating IPOP socket')
            sys.exit(1)
        self.ipop_listener.bind(('127.0.0.1', 55123))

        try:
            self.styx_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except:
            log.critical('error creating Styx socket')
            sys.exit(1)

        # TODO: parse the strongswan config file for the styx socket path
        socket_filename = '/var/run/styx.sock'
        try:
            self.styx_socket.connect(socket_filename)
        except:
            log.critical('error connecting to styx socket. %s does not exist.' %
                         socket_filename)
            sys.exit(1)

        while True:
            # alternatively, push to queue, peek, pop when confirmation received
            todo = self.ipop_listener.recv(16).strip()

            self.styx_call('version', 'xx')
            result = self.styx_socket.recv(4096)
            log.info('todo = %s, result = %s', todo, result)
            # send styx message
            # acknowledge reply
