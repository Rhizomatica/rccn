#!/bin/bash

RHIZO_DIR="/var/rhizomatica/rrd"

AGES="12h 1d 1w 1m"

for age in $AGES; do

rrdtool graph $RHIZO_DIR/graphs/loadaverage-$age.png --start -$age -aPNG --units-exponent 0 -w 600 -t "Load Average" \
"DEF:ds1=$RHIZO_DIR/loadaverage.rrd:load1:AVERAGE" \
"DEF:ds2=$RHIZO_DIR/loadaverage.rrd:load5:AVERAGE" \
"DEF:ds3=$RHIZO_DIR/loadaverage.rrd:load15:AVERAGE" \
'HRULE:5.0#44B5FF' \
"AREA:ds3#FFEE00:Last 15 min\t" \
  'VDEF:max1=ds3,MAXIMUM' \
  'VDEF:min1=ds3,MINIMUM' \
  'VDEF:avg1=ds3,AVERAGE' \
  GPRINT:max1:"Max %6.2lf" \
  GPRINT:min1:"Min %6.2lf" \
  GPRINT:avg1:"Avg %6.2lf\n" \
"LINE3:ds2#FFCC00:Last 5 min \t" \
  'VDEF:max2=ds2,MAXIMUM' \
  'VDEF:min2=ds2,MINIMUM' \
  'VDEF:avg2=ds2,AVERAGE' \
  GPRINT:max2:"Max %6.2lf" \
  GPRINT:min2:"Min %6.2lf" \
  GPRINT:avg2:"Avg %6.2lf\n" \
"LINE1:ds1#FF0000:Last 1 min \t" \
  'VDEF:max3=ds1,MAXIMUM' \
  'VDEF:min3=ds1,MINIMUM' \
  'VDEF:avg3=ds1,AVERAGE' \
  GPRINT:max3:"Max %6.2lf" \
  GPRINT:min3:"Min %6.2lf" \
  GPRINT:avg3:"Avg %6.2lf\n"

rrdtool graph $RHIZO_DIR/graphs/cpu-$age.png --start -$age -aPNG -w 600 -l 0 -u 100 -M -t "CPU Usage" \
"DEF:uj=$RHIZO_DIR/cpu.rrd:user:AVERAGE" \
"DEF:nj=$RHIZO_DIR/cpu.rrd:nice:AVERAGE" \
"DEF:sj=$RHIZO_DIR/cpu.rrd:sys:AVERAGE" \
"DEF:ij=$RHIZO_DIR/cpu.rrd:idle:AVERAGE" \
'CDEF:l=uj,0.1,0.1,IF' \
'CDEF:tj=uj,nj,+,sj,+,ij,+' \
'CDEF:usr=100,uj,*,tj,/' \
'CDEF:nic=100,nj,*,tj,/' \
'CDEF:sys=100,sj,*,tj,/' \
'CDEF:idl=100,ij,*,tj,/' \
'CDEF:tot=100,tj,*,tj,/' \
'AREA:nic#0040A2:Nice  ' \
  'VDEF:maxN=nic,MAXIMUM' \
  'VDEF:minN=nic,MINIMUM' \
  'VDEF:avgN=nic,AVERAGE' \
  'VDEF:curN=nic,LAST' \
  GPRINT:curN:"Current\: %6.2lf%%" \
  GPRINT:maxN:"Max %6.2lf%%" \
  GPRINT:minN:"Min %6.2lf%%" \
  GPRINT:avgN:"Avg %6.2lf%%\n" \
'AREA:sys#90C5CC:System:STACK' \
'LINE2:l#70A5AC::STACK' \
  'VDEF:maxS=sys,MAXIMUM' \
  'VDEF:minS=sys,MINIMUM' \
  'VDEF:avgS=sys,AVERAGE' \
  'VDEF:curS=sys,LAST' \
  GPRINT:curS:"Current\: %6.2lf%%" \
  GPRINT:maxS:"Max %6.2lf%%" \
  GPRINT:minS:"Min %6.2lf%%" \
  GPRINT:avgS:"Avg %6.2lf%%\n" \
'AREA:usr#B0E5EC:User  :STACK' \
'LINE2:l#90C5CC::STACK' \
  'VDEF:maxU=usr,MAXIMUM' \
  'VDEF:minU=usr,MINIMUM' \
  'VDEF:avgU=usr,AVERAGE' \
  'VDEF:curU=usr,LAST' \
  GPRINT:curU:"Current\: %6.2lf%%" \
  GPRINT:maxU:"Max %6.2lf%%" \
  GPRINT:minU:"Min %6.2lf%%" \
  GPRINT:avgU:"Avg %6.2lf%%\n"  \
'AREA:idl#EEFFFF:Idle  :STACK' \
  'VDEF:maxI=idl,MAXIMUM' \
  'VDEF:minI=idl,MINIMUM' \
  'VDEF:avgI=idl,AVERAGE' \
  'VDEF:curI=idl,LAST' \
  GPRINT:curI:"Current\: %6.2lf%%" \
  GPRINT:maxI:"Max %6.2lf%%" \
  GPRINT:minI:"Min %6.2lf%%" \
  GPRINT:avgI:"Avg %6.2lf%%\n"

rrdtool graph $RHIZO_DIR/graphs/temperature-$age.png --start -$age -aPNG --slope-mode -w 600 -t "Temperature" --vertical-label "temperature (°C)" DEF:temp1=$RHIZO_DIR/temperature.rrd:temp:MAX LINE1:temp1#ff0000:"Temperature"


rrdtool graph $RHIZO_DIR/graphs/memory-$age.png --start -$age -aPNG -w 600 -t "Memory Usage" \
"DEF:dsC=$RHIZO_DIR/memory.rrd:cached:AVERAGE" \
"DEF:dsB=$RHIZO_DIR/memory.rrd:buffer:AVERAGE" \
"DEF:dsF=$RHIZO_DIR/memory.rrd:free:AVERAGE" \
"DEF:dsT=$RHIZO_DIR/memory.rrd:total:AVERAGE" \
'CDEF:tot=dsT,1024,*' \
'CDEF:fre=dsF,1024,*' \
'CDEF:freP=fre,100,*,tot,/' \
'CDEF:buf=dsB,1024,*' \
'CDEF:bufP=buf,100,*,tot,/' \
'CDEF:cac=dsC,1024,*' \
'CDEF:cacP=cac,100,*,tot,/' \
'CDEF:use=dsT,dsF,dsC,+,dsB,+,-,1024,*' \
'CDEF:useP=use,100,*,tot,/' \
'CDEF:l=use,1,1,IF' \
'AREA:use#CC3300:User   ' \
'LINE2:l#AC1300::STACK' \
  'VDEF:maxU=use,MAXIMUM' \
  'VDEF:minU=use,MINIMUM' \
  'VDEF:avgU=use,AVERAGE' \
  'VDEF:curU=use,LAST' \
  'VDEF:procU=useP,LAST' \
  GPRINT:curU:"Last %6.2lf %s" \
  GPRINT:procU:"%3.0lf%%" \
  GPRINT:avgU:"Avg %6.2lf %s" \
  GPRINT:maxU:"Max %6.2lf %s" \
  GPRINT:minU:"Min %6.2lf %s\n" \
'AREA:cac#FF9900:Cached :STACK' \
'LINE2:l#DF7900::STACK' \
  'VDEF:maxC=cac,MAXIMUM' \
  'VDEF:minC=cac,MINIMUM' \
  'VDEF:avgC=cac,AVERAGE' \
  'VDEF:curC=cac,LAST' \
  'VDEF:procC=cacP,LAST' \
  GPRINT:curC:"Last %6.2lf %s" \
  GPRINT:procC:"%3.0lf%%" \
  GPRINT:avgC:"Avg %6.2lf %s" \
  GPRINT:maxC:"Max %6.2lf %s" \
  GPRINT:minC:"Min %6.2lf %s\n" \
'AREA:buf#FFCC00:Buffers:STACK' \
'LINE2:l#DFAC00::STACK' \
  'VDEF:maxB=buf,MAXIMUM' \
  'VDEF:minB=buf,MINIMUM' \
  'VDEF:avgB=buf,AVERAGE' \
  'VDEF:curB=buf,LAST' \
  'VDEF:procB=bufP,LAST' \
  GPRINT:curB:"Last %6.2lf %s" \
  GPRINT:procB:"%3.0lf%%" \
  GPRINT:avgB:"Avg %6.2lf %s" \
  GPRINT:maxB:"Max %6.2lf %s" \
  GPRINT:minB:"Min %6.2lf %s\n" \
'AREA:fre#FFFFCC:Unused :STACK' \
  'VDEF:maxF=fre,MAXIMUM' \
  'VDEF:minF=fre,MINIMUM' \
  'VDEF:avgF=fre,AVERAGE' \
  'VDEF:curF=fre,LAST' \
  'VDEF:procF=freP,LAST' \
  GPRINT:curF:"Last %6.2lf %s" \
  GPRINT:procF:"%3.0lf%%" \
  GPRINT:avgF:"Avg %6.2lf %s" \
  GPRINT:maxF:"Max %6.2lf %s" \
  GPRINT:minF:"Min %6.2lf %s\n"

rrdtool graph $RHIZO_DIR/graphs/disk-$age.png --start -$age -aPNG --vertical-label='MB' -w 600 -t "Disk Usage" -r -l 0 \
"DEF:roottotal=$RHIZO_DIR/disk.rrd:sizetot:AVERAGE" \
"DEF:rootused=$RHIZO_DIR/disk.rrd:sizeused:AVERAGE" \
'CDEF:bo=roottotal,UN,0,roottotal,IF,0,GT,UNKN,INF,IF' \
'AREA:bo#DDDDDD:' \
"AREA:rootused#190821" \
'CDEF:root=roottotal,0,+' \
'VDEF:sumr=root,LAST' \
GPRINT:sumr:"Total %0.2lf MB" \
'VDEF:lasr=rootused,LAST' \
GPRINT:lasr:"Used %0.2lf MB" \
'CDEF:rootPu=rootused,100,*,root,/' \
'VDEF:procr=rootPu,LAST' \
GPRINT:procr:"%0.2lf%%\\n" \
'CDEF:rootfree=roottotal,rootused,-' \
"AREA:rootfree#9933cc" \
'VDEF:lasr2=rootfree,LAST' \
GPRINT:lasr2:"Free %0.2lf MB" \
'CDEF:procar=rootfree,100,*,roottotal,/' \
'VDEF:procar2=procar,LAST' \
GPRINT:procar2:"%1.2lf%%"

rrdtool graph $RHIZO_DIR/graphs/eth0_traffic-$age.png --start -$age -aPNG -w 600 -t "Eth0 Interface Traffic" \
--rigid \
--base=1000 \
--alt-autoscale-max \
--lower-limit=0 \
--vertical-label="bits per second" \
--slope-mode \
DEF:a=$RHIZO_DIR/eth0.rrd:RX_bytes:AVERAGE \
DEF:b=$RHIZO_DIR/eth0.rrd:RX_bytes:LAST \
DEF:c=$RHIZO_DIR/eth0.rrd:RX_bytes:MIN \
DEF:d=$RHIZO_DIR/eth0.rrd:RX_bytes:MAX \
DEF:e=$RHIZO_DIR/eth0.rrd:TX_bytes:AVERAGE \
DEF:f=$RHIZO_DIR/eth0.rrd:TX_bytes:LAST \
DEF:g=$RHIZO_DIR/eth0.rrd:TX_bytes:MIN \
DEF:h=$RHIZO_DIR/eth0.rrd:TX_bytes:MAX \
CDEF:cdefa=a,8,* \
CDEF:cdefb=b,8,* \
CDEF:cdefd=d,8,* \
CDEF:cdefe=e,8,* \
CDEF:cdeff=f,8,* \
CDEF:cdefh=h,8,* \
AREA:cdefa#00CF00FF:"Inbound"  \
GPRINT:cdefb:LAST:"  Cur\\:%4.2lf %s"  \
GPRINT:cdefa:AVERAGE:"Avg\\:%4.2lf %s"  \
GPRINT:cdefd:MAX:"Max\\:%4.2lf %s\n"  \
LINE1:cdefe#002A97FF:"Outbound"  \
GPRINT:cdeff:LAST:"Cur\\:%4.2lf %s"  \
GPRINT:cdefe:AVERAGE:"Avg\\:%4.2lf %s" \
GPRINT:cdefh:MAX:"Max\\:%4.2lf %s" 


rrdtool graph $RHIZO_DIR/graphs/eth0_errors-$age.png --start -$age -aPNG --vertical-label='Errors' --lower-limit=0 -w 600 -t "Eth0 Interface Errors"  \
DEF:a=$RHIZO_DIR/eth0.rrd:RX_errors:AVERAGE \
DEF:b=$RHIZO_DIR/eth0.rrd:RX_drops:AVERAGE \
DEF:c=$RHIZO_DIR/eth0.rrd:RX_frame:AVERAGE \
DEF:d=$RHIZO_DIR/eth0.rrd:TX_errors:AVERAGE \
DEF:e=$RHIZO_DIR/eth0.rrd:TX_drops:AVERAGE \
DEF:f=$RHIZO_DIR/eth0.rrd:TX_carriers:AVERAGE \
DEF:g=$RHIZO_DIR/eth0.rrd:collisions:AVERAGE \
LINE1:a#FFAB00FF:"Errors In"  \
GPRINT:a:LAST:" Cur\:%4.2lf %s"  \
GPRINT:a:AVERAGE:"Avg\:%4.2lf %s"  \
GPRINT:a:MAX:"Max\:%4.2lf %s\n"  \
LINE1:b#F51D30FF:"Drops In"  \
GPRINT:b:LAST:"  Cur\:%4.2lf %s"  \
GPRINT:b:AVERAGE:"Avg\:%4.2lf %s"  \
GPRINT:b:MAX:"Max\:%4.2lf %s\n"  \
LINE1:c#C4FD3DFF:"Frame In"  \
GPRINT:c:LAST:"   Cur\:%4.2lf %s"  \
GPRINT:c:AVERAGE:"Avg\:%4.2lf %s"  \
GPRINT:c:MAX:"Max\:%4.2lf %s\n"  \
LINE1:d#00694AFF:"Errors Out"  \
GPRINT:d:LAST:"Cur\:%4.2lf %s"  \
GPRINT:d:AVERAGE:"Avg\:%4.2lf %s"  \
GPRINT:d:MAX:"Max\:%4.2lf %s\n"  \
LINE1:e#EE5019FF:"Drops Out"  \
GPRINT:e:LAST:" Cur\:%4.2lf %s"  \
GPRINT:e:AVERAGE:"Avg\:%4.2lf %s"  \
GPRINT:e:MAX:"Max\:%4.2lf %s\n"  \
LINE1:f#55009DFF:"Carriers Out"  \
GPRINT:f:LAST:"Cur\:%4.2lf %s"  \
GPRINT:f:AVERAGE:"Avg\:%4.2lf %s"  \
GPRINT:f:MAX:"Max\:%4.2lf %s\n"  \
LINE1:g#CCBB00FF:"Collisions"  \
GPRINT:g:LAST:"Cur\:%4.2lf %s"  \
GPRINT:g:AVERAGE:"Avg\:%4.2lf %s"  \
GPRINT:g:MAX:"Max\:%4.2lf %s\n"  


done
