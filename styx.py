'''
A wrapper around the styx JSON RPC.
'''

import socket
import logging
import json
import config

log = logging.getLogger('styx')

class Styx(object):
    def __init__(self, path):
        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except:
            log.critical('error creating Styx socket')
            sys.exit(1)

        try:
            self.socket.connect(path)
        except:
            log.critical('error connecting to Styx socket. %s does not exist' %
                         path)
            sys.exit(1)

        self.message_id = 0 # must be incremented every call

    @staticmethod
    def format(msg):
        msg = json.dumps(msg)
        if config.styx_message_length > 0:
            padding = ' ' * (config.styx_message_length-1-len(msg)) + '\0'
        else:
            padding = ''
        return msg + padding

    def call(self, method, *args):
        msg = self.format({
            'jsonrpc': '2.0',
            'method': method,
            'params': [json.dumps(a) for a in args],
            'id': self.message_id,
        })

        self.socket.sendall(msg)
        self.message_id += 1
        log.info('sent message to Styx: %s' % msg)

        result = json.loads(self.socket.recv(config.styx_message_length))
        log.info('received message from Styx: %s' % result)
        return result

    def __getattr__(self, method):
        '''
        Allows you to do something like: ``myStyxObj.addConfig(...)``, which
        will in return use :meth:`call`.
        '''
        def f(*args):
            return self.call(method, *args)
