#!/bin/bash

RHIZO_DIR="/var/rhizomatica/rrd"

AGES="12h 1d 1w 1m"

for age in $AGES; do

rrdtool graph --start -$age -v 'calls' -w 600 -t "Active Calls" $RHIZO_DIR/graphs/calls-$age.png \
"DEF:active_callsu=$RHIZO_DIR/fs_calls.rrd:calls:AVERAGE" \
'CDEF:active_calls=active_callsu,FLOOR' \
'AREA:active_calls#94D239:Calls' \
'LINE1:active_calls#569100' \
'GPRINT:active_calls:LAST:Current\:%.0lf %s'  \
'GPRINT:active_calls:AVERAGE:Average\:%.0lf %s'  \
'GPRINT:active_calls:MAX:Maximum\:%.0lf %s'

rrdtool graph --start -$age -v 'percentage' -w 600 --slope-mode -t "Channels Usage (%)" $RHIZO_DIR/graphs/chans-$age.png \
 DEF:sdcchu=$RHIZO_DIR/bsc_channels.rrd:sdcch:AVERAGE \
 CDEF:sdcch=sdcchu,FLOOR \
 DEF:tchu=$RHIZO_DIR/bsc_channels.rrd:tch:AVERAGE \
 CDEF:tch=tchu,FLOOR \
 LINE:sdcch#2AAAFF:"SDCCH           " \
 GPRINT:sdcch:LAST:"Current\:%6.0lf%%\t        "  \
 GPRINT:sdcch:AVERAGE:"Average\:%6.0lf%%\t       "  \
 GPRINT:sdcch:MAX:" Maximum\:%6.0lf%%\n" \
 LINE1:tch#F87D00:TCH \
 GPRINT:tch:LAST:"Current\:%6.0lf%%"  \
 GPRINT:tch:AVERAGE:"Average\:%6.0lf%%"  \
 GPRINT:tch:MAX:"Maximum\:%6.0lf%%" \

rrdtool graph --start -$age -v 'subscribers' -w 600 -t "Online registered subscribers" $RHIZO_DIR/graphs/hlr_onlinereg-$age.png \
"DEF:onlineu=$RHIZO_DIR/hlr.rrd:online_reg_subs:AVERAGE" \
'CDEF:online=onlineu,FLOOR' \
'AREA:online#7CBDFF:Online registered' \
'LINE:online#427AB3' \
'GPRINT:online:LAST:Current\:%6.0lf %s'  \
'GPRINT:online:AVERAGE:Average\:%6.0lf %s' \
"GPRINT:online:MAX:Maximum\:%6.0lf %s\n" \

rrdtool graph --start -$age -v 'subscribers' -w 600 -t "Online not registered subscribers" $RHIZO_DIR/graphs/hlr_onlinenoreg-$age.png \
"DEF:noregonlineu=$RHIZO_DIR/hlr.rrd:online_noreg_subs:AVERAGE" \
'CDEF:onlinenoreg=noregonlineu,FLOOR' \
'AREA:onlinenoreg#B4B4B4:Online not registered ' \
'LINE:onlinenoreg#666666' \
'GPRINT:onlinenoreg:LAST:Current\:%6.0lf %s' \
'GPRINT:onlinenoreg:AVERAGE:Average\:%6.0lf %s' \
'GPRINT:onlinenoreg:MAX:Maximum\:%6.0lf %s'


done

