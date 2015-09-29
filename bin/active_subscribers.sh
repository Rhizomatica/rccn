#!/bin/bash

site_name=`curl -X GET http://localhost:8085/configuration/site 2>/dev/null | python -mjson.tool | grep 'site_name' | cut -d: -f2 | tr -d '"' | tr -d ' '`
active_sub=`curl -X GET http://localhost:8085/subscriber/paid_subscription 2>/dev/null`

echo -e "Subject:[`date +"%B %Y"`] $site_name active subscribers: $active_sub" | sendmail "staff@lists.rhizomatica.org"
echo -e "`date +"%m-%Y"`,$active_sub" >> /var/rhizomatica/bin/active_subscribers.csv
