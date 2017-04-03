<?php 
require_once('include/header.php');
require_once('include/menu.php');
require_once('modules/credit.php');
$cred = new Credit();
$c_alloc=$cred->get_all_credit_allocated();
$c_both=$c_not_paid_auth=$c_paid_not_auth=$c_na=0;
foreach ($c_alloc as $row) {
	$auth=$row[0];
	$sub=$row[1];
	$amount=$row[2];
	if ($auth && $sub) {
		$c_both=$amount;
	} elseif (!$sub and $auth) {
		$c_not_paid_auth=$amount;
	} elseif ($sub and !$auth) {
		$c_paid_not_auth=$amount;
	} elseif (!$sub and !$auth) {
		$c_na=$amount;
	}
}
?>

		<script type="text/javascript" language="javascript">
			$(document).ready(function () {
			$.ajax({
    			    url: "get_balance.php",
		            type: "GET",
		            cache: false,
			    timeout: 60000,
			    error: function() {
				$('#balance').html("<span style='font-size: 20px; color: red'><?=_('Error loading VOIP Account Balance.. please try again later') ?>");
			    },
		   	    beforeSend:function(){
			       $('#balance').html('<img src="img/loading.gif" alt="Loading..." /><br/><br/><span style="font-size: 20px"><?=_('Loading VOIP Account Balance.. please wait') ?></span>');
			    },
		            success: function (html) {
			            $('#balance').html("<span style='font-size: 20px;'><?=_('VOIP Account Balance:')?> <b>" + html + "</b> USD</span>");
		            }
			 });
			
			});
		</script>
			<? print_menu('platform'); ?>	
			<br/><br/><br/><br/><br/><br/>
			<center>
			<?php
				echo "<img src='img/account.png' width='150' height='150' /><br/><br/>";
				echo "<div id='balance'></div>";
			?>
			<div id='credit' style="font-size: 16px;text-align: left; width: 300px; margin-top: 10px;"> 
			<?=_('Credit Allocated:')?>
			<div>
				<div><?=_('Authorised:')?> <b><?=$c_both?></b> MXN</div>
				<div><?=_('Not Authorised:')?> <b><?=$c_na?></b> MXN</div>
				<div><?=_('Not Paid, Authorised:')?> <b><?=$c_not_paid_auth?></b> MXN</div>
			</div>
			</div>

			</center>
		</div>
	</body>

</html>
