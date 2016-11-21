#!/bin/bash

RHIZO_DIR="/var/rhizomatica/rrd"

mybts=`echo "show bts" | nc localhost 4242 | grep BTS | awk '{ print $2 }'`

for bts in $mybts ; do
  eval _channels_$bts=`echo "show bts $bts" | nc localhost 4242 | awk 'BEGIN {tch=0;sdcch=0} /TCH\/F/ {tch=substr($0,33,1)}; /SDCCH8/ {sdcch=substr($0,33,1)} END {print tch":"sdcch}'`
done
rrdtool update $RHIZO_DIR/bts_channels60.rrd N:$_channels_0:$_channels_1:$_channels_2:$_channels_3:$_channels_4:$_channels_5

