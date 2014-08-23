#!/bin/bash
#
# To activate the remaining voip account balance notification to specific users add to cron:
# 0 */5  * *   *     root /var/rhizomatica/bin/check_account_balance.sh

MSISDN=( "68820132107" "68820122786" )
BALANCE=`/var/rhizomatica/bin/get_account_balance.sh`
OUT=`echo $BALANCE | awk '{if ($1 < 10) print $0}' | sed -e 's/\n//g'`

PORT=4242
HOST=localhost
PROMPT="OpenBSC>"

send_command() {
  (echo $* ; sleep 1 ) |
    telnet $HOST $PORT 2>&1 |
    sed '1,/'$PROMPT'/d;/'$PROMPT'/,$d'
}


if [ "$OUT" != "" ]; then
	# balance < 20 send SMS
	TEXT="El balance de la cuenta VOIP esta de bajo de los \$10. Balance Actual es: \$${BALANCE} USD"
	CLENGTH="${#TEXT}"

	for msisdn in ${MSISDN[@]}; do
		message_body="subscriber extension $msisdn sms sender extension 10000 send $TEXT"
		send_command $message_body
	done

fi

