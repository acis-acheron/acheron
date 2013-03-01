'''
A wrapper around the styx JSON RPC.
'''

import socket
import logging
import json
import config
import sys

log = logging.getLogger('styx')

class Styx(object):
    def __init__(self, path):
        self._path = path
        self.socket = None
        self.__reconnect()
        self.message_id = 0 # unique message id
    def __reconnect(self):
        if self.socket:
            self.socket.close()

        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except:
            log.critical('error creating Styx socket')
            sys.exit(1)

        try:
            self.socket.connect(self._path)
        except:
            log.critical('error connecting to Styx socket. %s does not exist' %
                         self._path)
            sys.exit(1)

    @staticmethod
    def format(msg):
        msg = json.dumps(msg)
        if config.styx_message_length > 0:
            padding = ' ' * (config.styx_message_length-1-len(msg)) + '\0'
        else:
            padding = ''
        return msg + padding

    def call(self, method, *args):
        msg = {
            'jsonrpc': '2.0',
            'method': method,
            'params': args,
            'id': self.message_id,
        }

        while True:
            try:
                self.socket.sendall(self.format(msg))
                log.info('sent message to Styx: %s' % msg)
                self.message_id += 1
                break
            except socket.error:
                log.info('socket closed from the other end. Reopening.')
                self.__reconnect()

        raw_result = self.socket.recv(config.styx_message_length)
        try:
            result = json.loads(raw_result)
        except:
            log.critical('failed to parse data from styx:\n' +
                         raw_result)
            return None
        log.info('received message from Styx: %s' % result)
        self.__reconnect()
        return result

    def __getattr__(self, method):
        '''
        Allows you to do something like: ``myStyxObj.addConfig(...)``, which
        will in return use :meth:`call`.
        '''
        return lambda *args: self.call(method, *args)
        
