'''
A wrapper around racoonctl, setkey, and all that stuff. Based on animal_control
for socialvpn.
'''

import string
import re
import logging
import subprocess
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

log = logging.getLogger('racoon')

warning_block = '''
# WARNING: The block below is automatically generated for use with acheron,
#          part of Contrail. It will be removed when acheron quits. Do not
#          attempt to edit this warning or anything below it in this file.

'''

config_template = '''
remote {remote} {{
    proposal {{
        encryption_algorithm aes;
        hash_algorithm sha256;
        authentication_method rsasig;
        dh_group 2;
    }}
    certificate_type x509 "{host_cert}" "{host_key}";
    my_identifier asn1dn;
    verify_identifier on;
    peers_identifier asn1dn;
    exchange_mode main;
}

sainfo {remote} {{
    authentication_algorithm hmac_sha1;
    compression_algorithm deflate;
    pfs_group 2;
    encryption_algorithm aes;
}}

'''

class Racoon(object):
    def __init__(self, racoon_conf_path, ipv4_addr, host_cert, host_key):
        self.racoon_conf_path = racoon_conf_path
        self.ipv4_addr = ipv4_addr
        self.host_cert = host_cert
        self.host_key = host_key
        self.peers = set()
        self.__cleaned_up = False
        try:
            # cleanup any possible remains of a previous run
            self.__config_cleanup()
        except LookupError:
            pass # we don't care if cleanup fails
        self.__config_init()

    def cleanup(self):
        '''
        Call this when you're done using the object. If you don't call this, it
        will happen automatically during garbage collection.
        '''
        if self.__cleaned_up:
            return
        self.__config_cleanup()
        for p in self.peers:
            self.__setkey_disassociate(p)
    
    def __del__(self):
        self.cleanup()

    def __config_init(self):
        log.debug('(re)initializing the racoon configuration')
        with open(self.racoon_conf_path, 'a') as f:
            f.write(warning_block)

    def __config_cleanup(self):
        '''
        Removes our comment and everything after it
        '''
        log.debug('cleaning up the racoon configuration')
        with open(self.racoon_conf_path, 'rw') as f:
            config_body = f.read()
            warning_index = string.rfind(config_body, warning_block)
            if warning_index < 0:
                raise LookupError(
                    'Cannot find our comment marker in configuration file'
                )
            f.seek(0); f.truncate(warning_index)

    def __racoonctl(self, *command):
        # TODO: Actually open the unix socket connection ourselves and do this
        subprocess.call(['racoonctl'] + command)
        # N.B. racoonctl always returns 1 on squeeze, so we just ignore it
    
    def __setkey_associate(ip_address):
        self.__setkey_spd('add', ip_address)

    def __setkey_disassociate(ip_address):
        self.__setkey_spd('delete', ip_address)

    def __setkey_spd(self, subcommand, ip_address):
        '''
        ``setkey`` is used to configure the security associations. This calls
        it.
        '''
        stdin = StringIO('''
            spd{sc} {l} {r} any -P out ipsec
                    esp/transport//require
                    ah/transport//require;
            spd{sc} {r} {l} any -P in ipsec
                    esp/transport//require
                    ah/transport//require;
        '''.format(sc=subcommand, l=self.ipv4_addr, r=ip_address))
        subprocess.check_call('setkey -c', stdin=stdin)
        log.debug('Wrote commands to setkey.\n')

    def __config_update(self):
        '''
        Rewrite the racoon configuration file with all the peers in self.peers
        '''
        log.debug('updating configuration file')
        # reset the configuration file to its base state
        self.__config_cleanup()
        self.__config_init()
        with open(self.racoon_conf_path, 'a') as config_file:
            e = self.__escape_str
            for peer in self.peers:
                config_file.write(config_template.format(
                    remote=peer, host_cert=e(self.host_cert),
                    host_key=e(self.host_key)
                ))
        log.debug('reloading configuration file with racoonctl')
        self.__racoonctl('reload-config')

    @staticmethod
    def __escape_str(unescaped):
        '''
        Racoon's configuration file might need certain strings to be escaped.
        This does that by converting a passed string to '\\xx' escaped form.
        '''
        def escape_char(c):
            return '\\{0:x}'.format(ord(c.group(0)))
        return re.sub("[^A-Za-z0-9_-/.]", escape_char, unescaped)

    def add_peer(ip_addr):
        self.peers.add(ip_addr)
        self.__config_update()
        self.__setkey_associate(ip_addr)

    def remove_peer(ip_addr):
        self.peers.remove(ip_addr)
        self.__setkey_disassociate(ip_addr)
        self.__config.update()
