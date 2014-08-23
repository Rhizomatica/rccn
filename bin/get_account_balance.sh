#!/bin/bash
# Write here the script to return the current balance for the voip account

USERNAME=""
PIN=""

#/usr/bin/curl -c /tmp/cookie.txt -L --data "p_sa=$USERNAME&p_pin=$PIN&p_nic=200&p_appname=reseller&p_formlang=english&dest=/account/reseller/english/splash.asp" "https://www.myaccountcenter.net/account/lookup.asp?WCI=login" 2>/dev/null | grep 'Funds Remaining' | awk -F'$' '{print $2}' | tr '</b>' ' '
