#!/bin/bash

#                                                                          #
# Note that currently osmo-msc does internal cleaning of the SMS database. #
# So for a split stack we probably do not want to run this script.         #
#                                                                          #

LOGFILE="/var/log/sms_cleanup.log"
SMS_DB="/var/lib/osmocom/hlr.sqlite3"
SMS_DB_BKP="/home/rhizomatica/sms/hlr_`date '+%d%m%Y'`.sqlite3"

function logc() {
	txt=$1
	echo "[`date '+%d-%m-%Y %H:%M:%S'`] $txt" >> $LOGFILE
}

logc "Run database cleanup. Current DB size: `ls -sh $SMS_DB | awk '{print $1}'`"
logc "Make backup copy of SMS db"
#cp -f $SMS_DB $SMS_DB_BKP

total_sms=`echo 'select count(*) from SMS;' | sqlite3 -init <(echo .timeout 1000) $SMS_DB`
total_sms_delivered=`echo 'select count(*) from SMS where sent is not null;' | sqlite3 -init <(echo .timeout 1000) $SMS_DB`
total_sms_old=`echo "select count(*) from SMS where created < datetime('now', '-4 day');" | sqlite3 -init <(echo .timeout 1000) $SMS_DB`

logc "Total SMS: $total_sms Delivered: $total_sms_delivered SMS older than 4 days: $total_sms_old"
logc "Cleanup DB"

# Delete Any Broadcast SMS to a subscriber that is currently not authorised and also has not been seen for two weeks.
echo "DELETE from SMS where src_ton=5 and exists (select * from subscriber where subscriber.extension = sms.dest_addr AND subscriber.expire_lu < datetime('now', '-14 day') and subscriber.authorized = 0);" | sqlite3 -init <(echo .timeout 1000) $SMS_DB
echo "DELETE from SMS where created < datetime(\"now\", \"-6 hours\") and sent is not null;" | sqlite3 -init <(echo .timeout 1000) $SMS_DB
echo "DELETE from SMS where created < datetime(\"now\", \"-7 day\") and src_ton=5 and sent is null;" | sqlite3 -init <(echo .timeout 1000) $SMS_DB
if [[ $(date +%d) == "1" ]]; then
  echo "DELETE from SMS where created < datetime(\"now\", \"-3 month\");" | sqlite3 -init <(echo .timeout 1000) $SMS_DB
fi

logc "DB size after cleanup: `ls -sh $SMS_DB | awk '{print $1}'`"
