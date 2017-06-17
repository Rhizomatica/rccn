<?php 
	require_once('include/header.php');
	require_once('include/menu.php');
?>

<style>
#credit_report {
	font: 1.65em "Lucida Grande", Verdana, Arial, Helvetica, sans-serif;
	margin: 0;
	padding: 0;
	color: #dcdcdc;
	background-color: #333;
}
#credit_report span {
    padding-left: 10px;
    width: 150px;
    display: inline-table;
}
</style>


<script language="Javascript">
$(function() {
	$('#cs_year').change()
});
</script>
	<? print_menu('credits'); ?>	

	<h1><?= _("Credit Status") ?></h1><br/>
	<div style="margin-left: 15px;">

<?= _("Year:");?> <select class="credit_status" id="cs_year" name="cs_year">
	<? $current_year=date('Y');
	for ($y=$current_year-9;$y<=$current_year;$y++) {
		$s=($y==$current_year) ? 'selected' : '';
		print '<option '.$s.' value="'.$y.'">'.$y.'</option>';
	} ?>
	</select>
<!--
<?= _("Month:");?> <select class="credit_status" id="cs_month" name="cs_month">
	<? $current_month=date('m');
    for( $i = 1; $i <=12; $i++ ) {
    	$month_num = str_pad( $i, 2, 0, STR_PAD_LEFT );
    	$s=($month_num==$current_month) ? 'selected' : '';
    	$month = strftime('%B', mktime(0, 0, 0, $i));
    	print '<option '.$s.' value="'.$month_num.'">'. $month.'</option>';
    } ?>
</select> -->

	</div>
	<div class="spacer"></div>

	<div id="dynamic">
			<div style="padding-bottom:10px;font-weight:bold;font-size: 12pt">
				<span style="margin-left: 10px"><?= _("Month");?></span>
				<span style="margin-left: 100px"><?= _("Credit Sold");?></span>
				<span style="margin-left: 50px"><?= _("Credit Used");?></span>
			</div>
		<div id="credit_report">

		</div>
	</div>
				
</div>
</body>
</html>
