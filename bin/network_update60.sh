#!/bin/bash

. /etc/profile.d/rccn-functions.sh

RHIZO_DIR="/var/rhizomatica/rrd"

for default in 0 1 2 3 4 5 ; do
  eval _channels_$default=0:0
done

mybts=`echo "show bts" | nc -q1 localhost 4242 | grep ^BTS | awk '{ print $2 }'`
echo $mybts > $RHIZO_DIR/mybts

trx=`echo "show trx" | nc -q1 0 4242 | grep Baseband.*OK | wc -l`
if [ "$trx" = "0" ] ; then
	# For some reason, it can fail, if 0, try once more, avoid false negative.
	trx=`echo "show trx" | nc -q1 0 4242 | grep Baseband.*OK | wc -l`
fi
echo $trx > /tmp/trxOK

ns=`ns | wc -l`
echo $ns > /tmp/gprs_ns

pdp=`pdpc`
echo $pdp > /tmp/pdp_contexts
rrdtool update $RHIZO_DIR/pdp_contexts.rrd N:$pdp

for bts in $mybts ; do
  eval _channels_$bts=`echo "show bts $bts" | nc -q1 localhost 4242 | awk 'BEGIN {tch=0;sdcch=0} /TCH\// {gsub("\\\(|\\\)","",$3) split($3,a,"\\\/"); tch=a[1]}; /SDCCH8/ { gsub("\\\(|\\\)","",$3) split($3,a,"\\\/"); sdcch=a[1] } END {print tch":"sdcch}'`
done
rrdtool update $RHIZO_DIR/bts_channels60.rrd N:$_channels_0:$_channels_1:$_channels_2:$_channels_3:$_channels_4:$_channels_5

