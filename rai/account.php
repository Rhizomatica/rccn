<?php 
require_once('include/header.php');
require_once('include/menu.php');
require_once('modules/credit.php');
$cred = new Credit();
$c_alloc=$cred->get_all_credit_allocated();
$rate=$cred->get_rate();
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
                        rate=<?=$rate?>;
                        mxn=parseInt(html*rate)
			            $('#balance').html("<span style='font-size: 20px;'><?=_('VOIP Account Balance:')?> <b>" + html + "</b> USD / <b>" + mxn + "</b> MXN</span>");
			            total=<?=number_format(($c_both+$c_not_paid_auth),2,'.','')?>;
			            diff=(mxn-total)
			            c="green"
			            if (diff<0) c="red"
			            $('#diff').html('<?=_('Credit Status')?>: <span style="color:'+c+';font-weight:bold">' + Math.abs(diff).toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, '$1,') + '</span> MXN');
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
			<div id='credit' style="font-size: 16px;text-align: left; width: 420px; margin-top: 10px; border-style: inset; border-width: 1px; border-radius: 7px;padding: 11px;"> 
			<?=_('Credit Allocated')?>:
			<div>
				<div><?=_('Authorised')?>: <b><?=number_format($c_both)?></b> MXN</div>
				<div><?=_('Not Authorised')?>: <b><?=number_format($c_na)?></b> MXN</div>
				<div><?=_('Not Paid, Authorised')?>: <b><?=number_format($c_not_paid_auth)?></b> MXN</div>
				<br />
				<div><?=_('Total Sold to Authorised Users')?>: <b><span id="ctotal"><?=number_format($c_both + $c_not_paid_auth,2)?></span></b> 
				MXN</div>
				<br />
				<div id="diff"></div>

			</div>
			</div>

			</center>
		</div>
	</body>

</html>
