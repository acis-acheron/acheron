#!/usr/bin/env python

from daemon import Daemon
import socket, sys

class Acheron(Daemon):
    def format_for_styx(self, msg):
        return msg + ' '*(4095-len(msg)) + '\0'

    def run(self):
        try:
            self.ipop_listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            sys.stderr.write('acheron: error creating IPOP socket\n')
            sys.exit(1)
        self.ipop_listener.bind(('127.0.0.1', 55123))

        try:
            self.styx_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except socket.error:
            sys.stderr.write('acheron: error creating Styx socket\n')
            sys.exit(1)

        # TODO: parse the strongswan config file for the styx socket path
        self.styx_socket.connect('/var/run/styx.sock')

        while True:
            # alternatively, push to queue, peek, pop when confirmation received
            todo = self.ipop_listener.recv(16).strip()
            self.styx_socket.sendall(self.format_for_styx('{"jsonrpc":"2.0", "method":"version", "params":["xx"], "id":0}'))
            result = self.styx_socket.recv(4096)
            f = open('/var/log/acheron.log', 'a+')
            print >> f, 'todo = ', todo, 'result = ', result
            f.flush()
            f.close()
            # send styx message
            # acknowledge reply
            
        
        
