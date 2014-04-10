#!/bin/bash

RHIZO_DIR="/var/rhizomatica/rrd"

rrdtool create $RHIZO_DIR/bsc_channels.rrd --step 300 \
DS:tch:GAUGE:600:0:U \
DS:sdcch:GAUGE:600:0:U \
RRA:AVERAGE:0.5:1:10080 \
RRA:MIN:0.5:1440:1 \
RRA:MAX:0.5:1440:1 \
RRA:MIN:0.5:10080:1 \
RRA:MAX:0.5:10080:1

rrdtool create $RHIZO_DIR/fs_calls.rrd --step 300 \
DS:calls:GAUGE:600:0:U \
RRA:AVERAGE:0.5:1:10080 \
RRA:MIN:0.5:1440:1 \
RRA:MAX:0.5:1440:1 \
RRA:MIN:0.5:10080:1 \
RRA:MAX:0.5:10080:1

rrdtool create $RHIZO_DIR/hlr.rrd --step 300 \
DS:online_reg_subs:GAUGE:600:0:U \
DS:online_noreg_subs:GAUGE:600:0:U \
RRA:AVERAGE:0.5:1:10080 \
RRA:MIN:0.5:1440:1 \
RRA:MAX:0.5:1440:1 \
RRA:MIN:0.5:10080:1 \
RRA:MAX:0.5:10080:1

