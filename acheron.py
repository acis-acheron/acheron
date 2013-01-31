#!/usr/bin/env python

from __future__ import print_function
import socket
import sys
import json
import logging

from daemon import Daemon
import config

log = logging.getLogger('acheron')

class Acheron(Daemon):
    def __init__(self, *args, **kwargs):
        Daemon.__init__(self, *args, **kwargs)
        self.styx_id = 0

    @staticmethod
    def format_for_styx(msg):
        msg = json.dumps(msg)
        if config.styx_message_length > 0:
            padding = ' ' * (config.styx_message_length-1-len(msg)) + '\0'
        else:
            padding = ''
        return msg + padding

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
        self.ipop_listener.bind((config.ipop_host, config.ipop_port))

        try:
            self.styx_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except:
            log.critical('error creating Styx socket')
            sys.exit(1)

        try:
            self.styx_socket.connect(config.styx_unix_socket_path)
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
