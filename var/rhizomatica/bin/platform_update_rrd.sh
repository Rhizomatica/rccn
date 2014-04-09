#!/bin/bash

RHIZO_DIR="/var/rhizomatica/rrd"

loadaverage=`cat /proc/loadavg | awk '{print $1":"$2":"$3}'`
rrdtool update $RHIZO_DIR/loadaverage.rrd N:$loadaverage

cpustat=`cat /proc/stat|head -1| sed "s/^cpu\ \+\([0-9]*\)\ \([0-9]*\)\ \([0-9]*\)\ \([0-9]*\).*/\1:\2:\3:\4/"`
rrdtool update $RHIZO_DIR/cpu.rrd N:$cpustat

temperature=`sensors | grep temp1: | head -1 | awk '{print $2}' | sed -e 's/°C//g' -e 's/\+//g'`
rrdtool update $RHIZO_DIR/temperature.rrd N:$temperature

C=$(egrep ^Cached /proc/meminfo|awk '{print $2}')
B=$(egrep ^Buffers /proc/meminfo|awk '{print $2}')
F=$(egrep ^MemFree /proc/meminfo|awk '{print $2}')
T=$(egrep ^MemTotal /proc/meminfo|awk '{print $2}')
ST=$(egrep ^SwapTotal /proc/meminfo|awk '{print $2}')
SF=$(egrep ^SwapFree /proc/meminfo|awk '{print $2}')
memupdate="${C}:${B}:${F}:${T}:${ST}:${SF}"
rrdtool update $RHIZO_DIR/memory.rrd N:$memupdate

DF=$(df -m|grep sda1 |awk '{print $2":"$3}')
#DI=$(cat /proc/partitions|grep sda1| awk '{print $5":"$6":"$7":"$8":"$9":"$10":"$11":"$12":"$13":"$14":"$15}'
rrdtool update $RHIZO_DIR/disk.rrd N:$DF

ethstats=`cat /proc/net/dev | grep eth0 | cut -d: -f2 | awk '{print $1":"$2":"$3":"$4":"$6":"$9":"$10":"$11":"$12":"$13":"$14 }'`
rrdtool update $RHIZO_DIR/eth0.rrd N:$ethstats

$RHIZO_DIR/../bin/platform_graph_rrd.sh > /dev/null
