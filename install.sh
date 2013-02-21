#!/bin/sh
rm -rf /opt/acheron
cp -r . /opt/acheron
cp -ra init.d/. /etc/init.d
update-rc.d ipsec defaults
update-rc.d acheron defaults
