#!/bin/sh
rm -rf /opt/acheron
cp -r . /opt/acheron
update-rc.d acheron defaults
