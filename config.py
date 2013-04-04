### Generic API Configuration ##################################################
# styx or racoon
backend = 'racoon'
cert_path = '/etc/ipsec.d/certs/myCert.pem'
priv_key_path = '/etc/ipsec.d/private/aliceKey.pem'

### Styx (StrongSwan) Configuration ############################################
# Unix socket to connect to styx with (this is currently hardcoded into styx)
styx_unix_socket_path = '/var/run/styx.sock'

# Styx has a bug where you have to ensure messages are a certain length. This
# is used to determine the proper amount of padding needed. If this bug gets
# fixed at some point in the future, 0 will disable the padding.
styx_message_length = 4096

### Racoon Configuration #######################################################
# The central configuration file for racoon that we'll modify
racoon_conf_path = '/etc/racoon/racoon.conf'

### IPOP Configuration #########################################################
# The host and port pair to connect to ipop with to find new peers
ipop_host = '127.0.0.1'
ipop_port = 55123
