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
        self.__cleaned_up = False

    def __reconnect(self):
        if self.socket:
            self.socket.close()

        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except:
            log.critical('error creating Styx socket')
            raise

        try:
            self.socket.connect(self._path)
        except:
            log.critical('error connecting to Styx socket. %s does not exist' %
                         self._path)
            raise

    def cleanup(self):
        if self.__cleaned_up: return
        if self.socket:
            self.socket.close()
        # Maybe do something else here?
        self.__cleaned_up = True

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

class StyxApi(Styx):
    '''
    Extends Styx to provide `add_peer` and `remove_peer` methods. This gives a
    consistant API across styx and racoon.
    '''
    def __init__(self, unix_socket_path, local_ip, cert_path, priv_key_path):
        Styx.__init__(self, unix_socket_path)
        self.local_ip = local_ip
        self.cert_path = cert_path
        self.priv_key_path = priv_key_path
        self.__connections = {}

    def add_peer(self, ip_addr):
        conn_id = 'conn_%d' % self.message_id
        self.addConfig(
            conn_id,
            self.local_ip,
            ip_addr,
            'leftcert=%s' % self.cert_path,
            'rightid=%any',
            'leftid=%any',
            'keyexchange=ikev2'
        )
        self.connect(False, conn_id)
        self.__connections[ip_addr] = conn_id

    def remove_peer(self, ip_addr):
        self.removeConfig(self.__connections[ip_addr])
