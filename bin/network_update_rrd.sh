#!/bin/bash

RHIZO_DIR="/var/rhizomatica/rrd"

channels=`echo "show network" | nc localhost 4242 | awk 'BEGIN {tch=0;sdcch=0} /TCH\/F/ {tch=$2}; /SDCCH8/ {sdcch=$2} ; {sub(/%/,"",tch); sub(/%/,"",sdcch)} END {print tch":"sdcch}'`
rrdtool update $RHIZO_DIR/bsc_channels.rrd N:$channels

calls=`fs_cli --timeout=5000 --connect-timeout=5000 -x 'show calls count' | grep total | awk '{print $1}'`
rrdtool update $RHIZO_DIR/fs_calls.rrd N:$calls

online_reg_subs=`echo "select count(*) from Subscriber where length(extension) = 11 and lac>0;" | sqlite3 /var/lib/osmocom/hlr.sqlite3`
online_noreg_subs=`echo "select count(*) from Subscriber where length(extension) = 5 and lac>0;" | sqlite3 /var/lib/osmocom/hlr.sqlite3`
rrdtool update $RHIZO_DIR/hlr.rrd N:$online_reg_subs:$online_noreg_subs

$RHIZO_DIR/../bin/network_graph_rrd.sh > /dev/null
