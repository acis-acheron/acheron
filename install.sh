#!/bin/sh
rm -rf /opt/acheron
cp -r . /opt/acheron
cp -ra init.d/. /etc/init.d
update-rc.d acheron defaults
