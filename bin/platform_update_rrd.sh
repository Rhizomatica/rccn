#!/bin/bash

RHIZO_DIR="/var/rhizomatica/rrd"

. /home/rhizomatica/bin/vars.sh

loadaverage=`cat /proc/loadavg | awk '{print $1":"$2":"$3}'`
rrdtool update $RHIZO_DIR/loadaverage.rrd N:$loadaverage

cpustat=`cat /proc/stat|head -1| sed "s/^cpu\ \+\([0-9]*\)\ \([0-9]*\)\ \([0-9]*\)\ \([0-9]*\).*/\1:\2:\3:\4/"`
rrdtool update $RHIZO_DIR/cpu.rrd N:$cpustat

temperature=`sensors 2>/dev/null | grep temp1: | head -1 | awk '{print $2}' | sed -e 's/°C//g' -e 's/\+//g'`
if [ -n "$temperature" ]; then
  rrdtool update $RHIZO_DIR/temperature.rrd N:$temperature
fi

linev=`/sbin/apcaccess status 2>/dev/null | grep LINEV | head -1 | awk '{print $3}'`
if [ -n "$linev" ]; then
  /usr/bin/rrdtool update $RHIZO_DIR/voltage.rrd N:$linev
  echo $linev > /tmp/voltage
fi

latency=`fping -t 1000 -i 250 -s -q -c4 "$LATENCY_HOST" 2>&1 | grep '(avg' | cut -d\  -f2`
if [ -n "$latency" ]; then
  echo $latency > /tmp/latency
  /usr/bin/rrdtool update $RHIZO_DIR/latency.rrd N:$latency
fi

C=$(egrep ^Cached /proc/meminfo|awk '{print $2}')
B=$(egrep ^Buffers /proc/meminfo|awk '{print $2}')
F=$(egrep ^MemFree /proc/meminfo|awk '{print $2}')
T=$(egrep ^MemTotal /proc/meminfo|awk '{print $2}')
ST=$(egrep ^SwapTotal /proc/meminfo|awk '{print $2}')
SF=$(egrep ^SwapFree /proc/meminfo|awk '{print $2}')
memupdate="${C}:${B}:${F}:${T}:${ST}:${SF}"
rrdtool update $RHIZO_DIR/memory.rrd N:$memupdate

if [ -n "$STAT_DISK" ]; then
  DF=$(df -m|grep $STAT_DISK |awk '{print $2":"$3}')
  rrdtool update $RHIZO_DIR/disk.rrd N:$DF
fi

if [ -n "$STAT_IF" ]; then
  ethstats=`cat /proc/net/dev | grep $STAT_IF | cut -d: -f2 | awk '{print $1":"$2":"$3":"$4":"$6":"$9":"$10":"$11":"$12":"$13":"$14 }'`
  rrdtool update $RHIZO_DIR/eth0.rrd N:$ethstats
fi
$RHIZO_DIR/../bin/platform_graph_rrd.sh > /dev/null
