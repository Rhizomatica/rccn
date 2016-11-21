#!/bin/sh

RHIZO_DIR="/var/rhizomatica/rrd"

if [ ! -f $RHIZO_DIR/bts_channels60.rrd ]; then
rrdtool create $RHIZO_DIR/bts_channels60.rrd --step 60 \
DS:tch0:GAUGE:120:0:U \
DS:sdcch0:GAUGE:120:0:U \
DS:tch1:GAUGE:120:0:U \
DS:sdcch1:GAUGE:120:0:U \
DS:tch2:GAUGE:120:0:U \
DS:sdcch2:GAUGE:120:0:U \
DS:tch3:GAUGE:120:0:U \
DS:sdcch3:GAUGE:120:0:U \
DS:tch4:GAUGE:120:0:U \
DS:sdcch4:GAUGE:120:0:U \
DS:tch5:GAUGE:120:0:U \
DS:sdcch5:GAUGE:120:0:U \
RRA:AVERAGE:0.5:1:10080 \
RRA:MIN:0.5:1440:1 \
RRA:MAX:0.5:1440:1 \
RRA:MIN:0.5:10080:1 \
RRA:MAX:0.5:10080:1

fi