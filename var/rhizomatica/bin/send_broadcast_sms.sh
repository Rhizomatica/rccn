#/bin/bash
extensions=`sqlite3 /var/lib/osmocom/hlr.sqlite3 "SELECT extension from Subscriber;"`

# Parameters for NITB:
PORT=4242
HOST=localhost
PROMPT="OpenBSC>"

# Parameters for BTS:
#PORT=4241
#HOST=localhost
#PROMPT="OsmoBTS>"

send_command() {
  # Echo command to the telnet interface and cut a header before the first
  # prompt and footer after the second prompt.
  # "sleep 1" is needed because otherwise telnet closes connection before
  # the command is executed.
  (echo $* ; sleep 1 ) |
    telnet $HOST $PORT 2>&1 |
    sed '1,/'$PROMPT'/d;/'$PROMPT'/,$d'
}

for EXT in $extensions; do message_body="subscriber extension $EXT sms sender extension 10000 send Buen dia Talea. Estaremos reestableciendo la telefonia celular comunitaria en los proximos dias. Gracias por su paciencia. [Rhizomatica]"; echo -e "Send SMS to $EXT" ; send_command $message_body; done

