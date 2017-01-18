#!/bin/bash

. /home/rhizomatica/bin/vars.sh

RHIZO_DIR="/var/rhizomatica/rrd"

AGES="3h 12h 1d 1w 1m 1y"

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
 LINE:sdcch#2AAAFF:"SDCCH            " \
 GPRINT:sdcch:LAST:"Current\:%6.0lf%%\t       "  \
 GPRINT:sdcch:AVERAGE:"Average\:%6.0lf%%\t      "  \
 GPRINT:sdcch:MAX:" Maximum\:%6.0lf%%\n" \
 LINE1:tch#F87D00:TCH \
 GPRINT:tch:LAST:"Current\:%6.0lf%%"  \
 GPRINT:tch:AVERAGE:"Average\:%6.0lf%%"  \
 GPRINT:tch:MAX:"Maximum\:%6.0lf%%" \

rrdtool graph --start -$age -v 'Channels' -w 600 --slope-mode -t "Broken Channels" $RHIZO_DIR/graphs/broken-$age.png \
 DEF:brokenm=$RHIZO_DIR/broken.rrd:broken:AVERAGE \
 LINE1:brokenm#2AAAFF:"Broken            " \
 GPRINT:brokenm:LAST:"Current\:%6.0lf\t       "  \
 GPRINT:brokenm:AVERAGE:"Average\:%6.0lf\t      "  \
 GPRINT:brokenm:MAX:" Maximum\:%6.0lf\n" \

for bts in 0 1 2 3 4 5; do 

_w=$(bname $bts)

rrdtool graph --start -$age -v 'Channels' -w 600 --slope-mode -t "$_w Ch. Usage (Absolute)." $RHIZO_DIR/graphs/chans-$bts-$age.png \
 DEF:sdcchu=$RHIZO_DIR/bts_channels60.rrd:sdcch$bts:AVERAGE \
 CDEF:sdcch=sdcchu,FLOOR \
 DEF:tchu=$RHIZO_DIR/bts_channels60.rrd:tch$bts:AVERAGE \
 CDEF:tch=tchu,FLOOR \
 LINE1:sdcch#2AAAFF:"SDCCH            " \
 GPRINT:sdcch:LAST:"Current\:%6.0lf\t        "  \
 GPRINT:sdcch:AVERAGE:"Average\:%6.0lf\t       "  \
 GPRINT:sdcch:MAX:" Maximum\:%6.0lf\n" \
 LINE1:tch#F87D00:"TCH" \
 GPRINT:tch:LAST:"Current\:%6.0lf"  \
 GPRINT:tch:AVERAGE:"Average\:%6.0lf"  \
 GPRINT:tch:MAX:"Maximum\:%6.0lf" \

done

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


rrdtool graph --start -$age -v 'requests' -w 600 -t 'Chan Requests per minute' $RHIZO_DIR/graphs/chanr-$age.png \
"DEF:cra=$RHIZO_DIR/stats.rrd:cr:AVERAGE" \
"DEF:crna=$RHIZO_DIR/stats.rrd:crn:AVERAGE" \
'CDEF:ccra=cra,60,*' \ 
'CDEF:ccrna=crna,60,*'  \
'LINE1:ccra#0066FF:Channel Requests' \
'LINE1:ccrna#ff0066:No Channel' \

rrdtool graph --start -$age -v 'lur' -w 600 -t 'LUR per minute' $RHIZO_DIR/graphs/lur-$age.png \
"DEF:lura=$RHIZO_DIR/stats.rrd:lur:AVERAGE" \
"DEF:lurra=$RHIZO_DIR/stats.rrd:lurr:AVERAGE" \
'CDEF:clura=lura,60,*' \
'CDEF:clurra=lurra,60,*' \
'LINE1:clura#0066FF:Accepted' \
'LINE1:clurra#ff0066:Rejected' \

rrdtool graph --start -$age -v 'sms' -w 600 -t 'SMS per minute' $RHIZO_DIR/graphs/sms-$age.png \
"DEF:moa=$RHIZO_DIR/stats.rrd:sms_mo:AVERAGE" \
"DEF:mta=$RHIZO_DIR/stats.rrd:sms_mt:AVERAGE" \
'CDEF:cmoa=moa,60,*' \ 
'CDEF:cmta=mta,60,*'  \
'LINE1:cmoa#0066FF:Mobile Originated' \
'LINE1:cmta#ff0066:Mobile Terminated' \
'GPRINT:cmoa:LAST:Most Recent\:%6.0lf %s' \
'GPRINT:cmta:LAST:Most Recent\:%6.0lf %s'    

 
rrdtool graph --start -$age -v 'calls' -w 600 -t 'Call Setup per minute' $RHIZO_DIR/graphs/calls-$age.png \
"DEF:amoc=$RHIZO_DIR/stats.rrd:moc:AVERAGE" \
"DEF:amoca=$RHIZO_DIR/stats.rrd:moca:AVERAGE" \ 
"DEF:amtc=$RHIZO_DIR/stats.rrd:mtc:AVERAGE" \
"DEF:amtca=$RHIZO_DIR/stats.rrd:mtca:AVERAGE" \ 
'CDEF:cmoa=amoc,60,*' \
'CDEF:cmta=amtc,60,*' \
'CDEF:cmoca=amoca,60,*' \
'CDEF:cmtca=amtca,60,*' \
'LINE1:cmoa#333300: Mobile Originated' \ 
'LINE1:cmta#669900: MO Connected' \
'LINE1:cmoca#993366: Mobile Terminated' \
'LINE1:cmtca#CC0099: MT Connected' \
'GPRINT:cmoa:LAST:Mobile Originated\:%6.0lf %s' 
'GPRINT:cmta:LAST:Mobile Terminated\:%6.0lf %s'


done

