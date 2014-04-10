<?php

function print_menu($select) {
	echo "<nav>";
	echo "<ul>";
	echo "<li><a href='logout.php'><img src='img/logout.png' width='10' height='10' /> "._("Logout")."</a></li>";
	echo "</ul>";

        echo "<ul>";
        $sel =  ($select == 'platform') ? 'class="menu_selected"' : '';
        echo "<li><a href='#' $sel>"._("Platform")."</a>";
	echo "<ul>";
        echo "<li><a href='site.php'>"._("Site")."</a></li>";
	echo "<li><a href='account.php'>"._("VOIP Account")."</a></li>";
	echo "<li><a href='platform_stats.php'>"._("System Stats")."</a></li>";
	echo "<li><a href='network_stats.php'>"._("Network Stats")."</a></li>";
	echo "</li>";
	echo "</ul>";

	$sel =  ($select == 'statistics') ? 'class="menu_selected"' : '';
        echo "<li><a href='' $sel>"._("Statistics")."</a>";
	echo "<ul>";
	echo "<li><a href='cost_stats.php'>"._("Costs")."</a></li>";
	echo "<li><a href='call_stats.php'>"._("Calls")."</a></li>";
	echo "</ul>";
	echo "</li>";

        /*$sel =  ($select == 'network') ? 'class="menu_selected"' : '';
        echo "<li><a href='#' $sel>Network</a>";
	echo "<ul>";
	echo "<li><a href='tmsi.php'>TMSIs</a></li>";
	echo "<li><a href='network_stats.php'>Traffic</a></li>";
	echo "<li><a href='logs.php'>Logs</a></li>";
	echo "</ul>";
	echo "</li>";*/
	
        $sel =  ($select == 'subscribers') ? 'class="menu_selected"' : '';
        echo "<li><a href='subscribers.php' $sel>"._("Subscribers")."</a>";
	echo "<ul>";
	echo "<li><a href='provisioning.php'>"._("Provisioning")."</a></li>";
	echo "</ul>";
	echo "</li>";

        $sel =  ($select == 'resellers') ? 'class="menu_selected"' : '';
        echo "<li><a href='resellers.php' $sel>"._("Resellers")."</a>";
        echo "<ul>";
        echo "<li><a href='resellers.php'>"._("List Resellers")."</a></li>";
        echo "<li><a href='resellers_provisioning.php'>"._("Provisioning")."</a></li>";
        echo "<li><a href='resellers_credit.php'>"._("Add Credit")."</a></li>";
	echo "<li><a href='resellers_credit_history.php'>"._("Resellers invoices")."</a></li>";
	echo "<li><a href='resellers_transactions.php'>"._("Transactions")."</a></li>";
        echo "<li><a href='resellers_configuration.php'>"._("Configuration")."</a></li>";
        echo "</ul>";
        echo "</li>";


	$sel =  ($select == 'credits') ? 'class="menu_selected"' : '';
        echo "<li><a href='' $sel>"._("Credits")."</a>";
	echo "<ul>";
	echo "<li><a href='credit.php'>"._("Add Credit")."</a></li>";
	echo "<li><a href='credit_history.php'>"._("History")."</a></li>";
	echo "</ul>";
	echo "</li>";

	$sel =  ($select == 'sms') ? 'class="menu_selected"' : '';
        echo "<li><a href='sms.php' $sel>"._("SMSs")."</a>";
	echo "<ul>";
	echo "<li><a href='send_sms.php'>"._("Send SMS")."</a></li>";
	echo "</ul>";
	echo "</li>";

        $sel =  ($select == 'cdr') ? 'class="menu_selected"' : '';
        echo "<li><a href='cdr.php' $sel>"._("CDRs")."</a></li>";

        $sel =  ($select == 'rates') ? 'class="menu_selected"' : '';
        echo "<li><a href='rates.php' $sel >"._("Rates")."</a></li>";


        echo '</ul>';
	echo "</nav>";
}
