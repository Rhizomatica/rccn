<?php
	exec("/var/rhizomatica/bin/get_account_balance.sh", $balance);
	echo $balance[0];
?>
