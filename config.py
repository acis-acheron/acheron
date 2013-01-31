# The unix socket to connect to styx with (this is hardcoded into styx)
styx_unix_socket_path = '/var/run/styx.sock'

# The host and port pair to connect to ipop with to find new peers
ipop_host = '127.0.0.1'
ipop_port = 55123

# Styx has a bug where you have to ensure messages are a certain length. This
# is used to determine the proper amount of padding needed. If this bug gets
# fixed at some point in the future, 0 will disable the padding.
styx_message_length = 4096
